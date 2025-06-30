# isq

A dependency-free Python library to represent both **units** and [**quantity kinds**](#tags) under the International System of Quantities (ISO/IEC 80000). 

**Goals**:

- provide objects for use in `typing.Annotated[T, x]`
- enable writing machine-readable, structured documentation
- no encapsulating numerical values in a new object
- optional, incremental adoption with immediate compatibility with external libraries
- lightweight, zero additional runtime performance overhead
- first-class support for [disambiguating units](#tags) (e.g. length vs. thickness vs. altitude)

**Limitation**: does not [(yet)](#dimension-checking) perform dimensional homogenity checks.


### Getting started

Install the library:

```sh
# with pip.
pip install https://github.com/cathaypacific8747/isq
# with uv.
uv add https://github.com/cathaypacific8747/isq
```

Since `isq` is designed to be documentation-first, you do not need to add `isq` as a required dependency if you don't need to use runtime features like [unit conversion](#unit-conversion), [simplification](#ast-and-simplification), [defining new units](#defining-new-units), [formatting](#formatting) or introspection. In that case, it is recommended to add `isq` to an [optional dependency group](https://docs.astral.sh/uv/concepts/projects/dependencies/#optional-dependencies) instead.

<details>

<summary>Documentation-only library installation and usage</summary>

```sh
uv add https://github.com/cathaypacific8747/isq --optional typing
```

Since `isq` is no longer a required depedency, put `isq` imports in the `typing.TYPE_CHECKING` block. Example:

```py
from __future__ import annotations

from typing import Any, Annotated, TYPE_CHECKING

if TYPE_CHECKING:
    from isq import N, KG, M, S

def acceleration(
    force: Annotated[Any, N],
    mass: Annotated[Any, KG]
) -> Annotated[Any, M * S**-2]:
    ...
```

</details>

See the [documentation](https://cathaypacific8747.github.io/isq) for more usage examples.


## Usage

Inspired by libraries like [`pydantic`](https://github.com/pydantic/pydantic) and [`annotated-types`](https://github.com/annotated-types/annotated-types), the recommended way to adopt `isq` is via `typing.Annotated[T, x]` (see [PEP 593](https://typing.python.org/en/latest/spec/qualifiers.html#annotated)):
```py
from typing import Any, Annotated
from isq import N, KG, M, S
def acceleration(
    force: Annotated[Any, N],
    mass: Annotated[Any, KG]
) -> Annotated[Any, M * S**-2]:
    ...
```

- unlike other libraries like [`pint`](https://github.com/hgrecco/pint), this library does not wrap your types in a new `Quantity` object
- type is kept intact as `T`
- delegates dimensionality checking to an [optional dimension-checking tool](#dimension-checking)
- powerful introspection:
    <details>
    <summary>Example</summary>

    ```pycon
    >>> from typing import get_type_hints
    >>> for arg, arg_type in get_type_hints(acceleration, include_extras=True).items():
    ...     print(f"{arg:>7} | {arg_type.__metadata__[0]}")
    ...
     force | newton
      mass | kilogram
    return | meter · second⁻²
    ```
    </details>

- centralised source of truth: reduces need for duplicate docstrings while supporting documentation generators like `mkdocstrings-python` (intersphinx [here](https://cathaypacific8747.github.io/isq/objects.inv))
- use in fields of a container: `dataclass`, `TypedDict`, `pydantic.BaseModel`...

### AST and simplification

Units are represented as immutable expression trees. The `isq.simplify` function canonicalises it into a flat form:
```pycon
>>> from isq.us_customary import PSI
>>> print(PSI)
psi
- psi = lbf · inch⁻²
  - lbf = pound · 9.80665 · (meter · second⁻²)
    - pound = 0.45359237 · kilogram
  - inch = 1/12 · foot
    - foot = 0.3048 · meter
>>> from isq import simplify
>>> print(simplify(PSI))
0.45359237 · 9.80665 · (1/12)⁻² · 0.3048⁻² · (kilogram · meter⁻¹ · second⁻²)
>>> print(simplify(PSI).dimension)
L⁻¹ · M · T⁻²
```
Note that the final scaling factor is not eagerly evaluated. This enables users to choose between approximate and exact arithmetic (useful for financial applications).

### Unit conversion

The `convert` function returns a callable that allow you to convert between compatible units.
```pycon
>>> from isq import M, S, MIN, convert
>>> from isq.us_customary import FT
>>> fpm2mps = convert(FT * MIN**-1, M * S**-1)
>>> fpm2mps
Converter(scale=0.00508, offset=0.0)
>>> fpm2mps(7200.0)
36.576
>>> convert(M, FT, exact=True)(11000)
Fraction(13750000, 381)
>>> convert(FT * MIN**-1, M * S**-2)  # velocity -> acceleration fails
isq.core.DimensionMismatchError: cannot convert from `foot · minute⁻¹
- foot = 0.3048 · meter
- minute = 60 · second` to `meter · second⁻²`.
help: expected compatible dimensions, but found:
dimension of origin: `L · T⁻¹`
dimension of target: `L · T⁻²`
```
The callable is compatible with many libraries, including `numpy.array` inputs and functional transformations like `jax.grad`/`jax.jit`.

### Defining new units

Code-as-data: all units are defined with Python without DSL/parsing an external file. Create your own units easily:
```pycon
>>> from fractions import Fraction
>>> from isq import M, convert, simplify
>>> from isq.us_customary import FT
>>> SMOOT = ((5 + Fraction(7, 12)) * FT).alias("smoot")
>>> print(SMOOT)
smoot
- smoot = 67/12 · foot
  - foot = 0.3048 · meter
>>> convert(SMOOT, M, exact=True)(Fraction("364.4"))
Fraction(7751699, 12500)
>>> print(simplify(SMOOT**2))
(67/12)² · 0.3048² · meter²
```

### Tags

Units alone are often insufficient to describe a quantity. Consider we might want to represent:

| Dimension                                      | Possible Quantity Kinds                                                                                              |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| $\text{L}$                                     | *geopotential altitude* / *geometric altitude* / *wingspan* / *chord length* / *radius* / *thickness* / *wavelength* |
| $\text{L}\text{T}^{-1}$                        | *indicated* / *true* / *ground* speed                                                                                |
| $\text{L}^2\text{M}\text{T}^{-3}\text{I}^{-1}$ | *RMS* / *peak-to-peak* voltage                                                                                       |
| $\text{L}^2\text{M}\text{T}^{-2}$              | *internal* / *kinetic* / *potential* / *enthalpy* / *Gibbs free* energy / *work done* / *heat* / *moment of force*   |
| $\text{\$}$                                    | *nominal* / *real* USD / *capex* / *opex*                                                                            |
| $\text{N}$                                     | moles of *hydrogen* / *oxygen* / *(arbitrary compound)*                                                              |
| $\text{T}^{-1}$                                | Hertz (unit of frequency) / Becqurel (unit of radionuclide activity)                                                 |

And that particular quantity kind may also refer to a specific:

- *inertial* / *body* / *stability* reference frame
- *x* / *y* / *z* direction
- location *A* / *B* / *C*...

Many quantities often share the same unit and we need a way to disambiguate between them. `isq.Tagged` allows you to constrain an existing unit with arbitary metadata:
```pycon
>>> from isq import MOL, Tagged, simplify, convert
>>> MOL_H2_L = Tagged(MOL, ("H_2", "liquid"))
>>> MOL_O2_G = Tagged(MOL, ("O_2", "gas"))
>>> print(simplify(MOL_H2_L * MOL_O2_G**-1).dimension) # NOT dimensionless!
N['H_2', 'liquid'] · (N['O_2', 'gas'])⁻¹
>>> convert(MOL_H2_L, MOL_O2_G)  # mismatched tags
isq.core.DimensionMismatchError: cannot convert from `mole['H_2', 'liquid']` to `mole['O_2', 'gas']`.
help: expected compatible dimensions, but found:
dimension of origin: `N['H_2', 'liquid']`
dimension of target: `N['O_2', 'gas']`
```

`Tagged` is effectively a newtype wrapper which contain hashable objects, such as strings or frozen dataclasses.

Internally, the library also makes use of `Tagged` to represent different logarithmic quantities. A decibel is the logarithm of some generic ratio, and a decibel-milliwatt refers to the *power* relative to 1 milliwatt: `Tagged` essentially constrains what the decibel is referring to.
```pycon
>>> from isq import DBM, DBW, convert
>>> print(DBM)
dBm
- dBm = 10 · log₁₀(ratio[`watt` relative to `(milliwatt)`])
  - watt = joule · second⁻¹
    - joule = newton · meter
      - newton = kilogram · meter · second⁻²
>>> convert(DBW, DBM)(10)
40.0
```

<!-- Similarly, for a generic *Reynolds number*, you may want to specify the *characteristic length* to be the *chord length* or *pipe diameter*. -->

### Quantity Kinds

The `Tagged` class is useful, but it forces downstream users to use a specific unit system. A more generic `isq.QtyKind` allows you to define an "abstract concept", which can be narrowed down to an compatible unit (U.S. customary, SI...):

```pycon
>>> from isq.aerospace import TAS, IAS
>>> TAS
QtyKind(unit_si=..., context=('airspeed', 'true'))
>>> from isq.us_customary import KNOT
>>> print(TAS[KNOT])
knot['airspeed', 'true']
- knot = nautical_mile · hour⁻¹
  - nautical_mile = 1852 · meter
  - hour = 60 · minute
    - minute = 60 · second
>>> from isq import simplify, convert, M, S
>>> convert(TAS[KNOT], TAS[M * S**-1])  # succeeds because context matches
Converter(scale=0.5144444444444445, offset=0.0)
```

### Formatting

All expressions implement `__format__`, which interally calls the `isq.fmt` function with a default `isq.BasicFormatter`.

It can also take in any formatter, supporting fine-grained control over display names, output formats and locales. To use shorter symbols or $\LaTeX$:
```pycon
>>> from isq import N, fmt, BasicFormatter
>>> f"{N}" == fmt(N, BasicFormatter(verbose=True))
True
>>> print(fmt(N, BasicFormatter(
...     verbose=True,
...     overrides={
...         "newton": "N",
...         "kilogram": "kg",
...         "meter": "m",
...         "second": "s"
...     },
... )))
N
- N = kg · m · s⁻²
>>> # TODO: latex once implemented
```

Internally, the basic formatter uses `isq.Visitor` to traverse each node in post-order. You can pass in your own formatter as long as it adheres to the `isq.Formatter` protocol.

## TODOs

- support more string representations (e.g. LaTeX)
  - compile LaTeX to SVG and manipulate symbols
- mindmap

### Dimension checking

Right now, using `Annotated[T, x]` without actually checking `x` is just glorified comments. For this library to be truly useful, it should perform static analysis to avoid unit mismatches. Such a tool is not yet implemented.

One possible path is to use tracer objects that record operations just-in-time, and error out when dimensions do not match. But this is extremely difficult for several reasons:

- it is common for a `numpy.NDArray` or `polars.DataFrame` to represent different units for each row/column.
  - determining the units for the matmul between two arrays is very difficult.
- interfacing with complex function transformations like `jax.grad(f)(x)` and `numpy.fft.fft` require significant maintenance burden.

Moving forward, the first MVP should start with simple function boundary checks, *only* at points where data crosses a declared "unit boundary" (argument passing, return statements). This alone would already cover most usecases.

Intra-expression errors (e.g. `distance_m + time_s`) are significantly more difficult to deal with and come much later.

Such a tool will be released as an optional feature, separate from the core library.

