# isq

A dependency-free Python library providing metadata objects defined by the
International System of Quantities (ISO/IEC 80000) and other subfields, including:

- units (`kg`, `ft`, `dB`...), and perhaps more importantly,
- extensible [quantity kinds](#quantity-kinds) (geopotential/geometric altitude,
  internal energy/work/heat...),
- optional utilities: unit [conversion](#unit-conversion),
  [simplification](#simplification) and [formatting](#formatting).

`isq` prioritises:

- zero performance overhead
- incremental, optional adoption of [annotations](#tutorial-documenting-code-with-type-annotations)
- immediate interoperability with external libraries
- extensibility
- support for exact/"jittable" unit conversion
- good LSP support

`isq` does not "wrap" a numerical type with the unit, and does **not** enforce
correctness at runtime.

It enables you to write documentation in an alternative way, using centralised
metadata objects that are machine-readable. *Enforcement* of correctness may
(or may not) come later as a separate, opt-in static analyzer.

## Installation

```sh
# with pip.
pip install https://github.com/abc8747/isq
# with uv.
uv add https://github.com/abc8747/isq
```

`isq` is designed to be documentation-first and can be used
[without introducing a hard dependency on your project](#quick-note-on-hard-dependencies).
You can find more examples, search the list of units/quantity kinds and find the
API reference in the [documentation](https://abc8747.github.io/isq/).

## Tutorial: Documenting code with type annotations

Most libraries use docstrings for simplicity. `isq` recommends incrementally adopting [PEP 593](https://typing.python.org/en/latest/spec/qualifiers.html#annotated).

First, define generic types that you will use throughout the codebase:

```py
# isq_types.py
from typing import Annotated, TypeVar

import isq

_T = TypeVar("_T")
M = Annotated[_T, isq.M]
K = Annotated[_T, isq.K]
Pa = Annotated[_T, isq.PA]
```
Annotate function arguments or data containers like `dataclasses`:

```py
# in another file
from .isq_types import M, K, Pa

def pressure_isa(altitude: M, isa_dev: K) -> Pa:
    # static checkers will show the type of `altitude` as `Unknown`
    ...

# or, if you prefer stricter typing:
from numpy.typing import ArrayLike

def pressure_isa(altitude: M[ArrayLike], isa_dev: K[ArrayLike]) -> Pa[ArrayLike]:
    # `altitude` now expects the type `ArrayLike` (not a wrapper over it!) 
    ...

from dataclasses import dataclass

@dataclass
class GasState:
    temperature: K
    pressure: Pa
```
Since annotations are ignored by the Python interpreter at runtime, and
`Annotated[T, x]` is equivalent to `T`, there is no interoperability cost.
Internally, unit objects are defined by composing with each other:
`J = (N * M).alias("joule")` and `N = (KG * M * S**-2).alias("newton")`.

You can also retrieve the annotations at runtime:
```py
from typing import get_type_hints

def print_metadata(obj):
    for param, hint in get_type_hints(obj, include_extras=True).items():
        print(f"`{param}`: {hint.__metadata__[0]}")

print_metadata(pressure_isa)
# `altitude`: meter
# `isa_dev`: kelvin
# `return`: pascal
# - pascal = newton · meter⁻²
#   - newton = kilogram · meter · second⁻²
print_metadata(GasState)
# `temperature`: kelvin
# `pressure`: pascal
# - pascal = newton · meter⁻²
#   - newton = kilogram · meter · second⁻²
```
___

But there is a flaw in using units alone:
![](docs/assets/img/readme_meters.drawio.svg)

`isq` encourages you to use a more abstract **quantity kind**, which can contain
arbitrary *tags* that store important metadata.

```py
from typing import Annotated, TypeVar

import isq

# note that `isq` provides *runtime objects*, not types.
# define generic types that can be used throughout your codebase
_T = TypeVar("_T")
GeopAltM = Annotated[_T, isq.aerospace.GEOPOTENTIAL_ALTITUDE(isq.M)]
TempDevIsaK = Annotated[_T, isq.aerospace.TEMPERATURE_DEVIATION_ISA(isq.K)]
StaticPressurePa = Annotated[_T, isq.STATIC_PRESSURE(isq.PA)]

def pressure_isa(altitude: GeopAltM, isa_dev: TempDevIsaK) -> StaticPressurePa:
    ...

# altitude: meter['altitude', relative to `'mean_sea_level'`, 'geopotential']
# isa_dev: kelvin['static', Δ, relative to `288.15 · kelvin`]
# return: pascal['static']
# - pascal = newton · meter⁻²
#   - newton = kilogram · meter · second⁻²
```

To create your own quantity kinds, see [below](#tutorial-creating-your-own-units-and-quantity-kinds).

### Quick note on hard dependencies

If you intend to use `isq` for documenting code only (without runtime features
like [conversions](#unit-conversion) or [simplification](#simplification)
, which we will explore below), it is recommended to make `isq` an
[optional dependency](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#dependencies-optional-dependencies)
of your project instead:

```sh
uv add https://github.com/abc8747/isq --optional typing
```
Put `isq` imports within the `typing.TYPE_CHECKING` block:

```py
from __future__ import annotations  # see PEP 563, PEP 649

from typing import Annotated, TYPE_CHECKING

if TYPE_CHECKING:
    import isq

    FloatM = Annotated[float, isq.M]  # or put them in a separate module

def foo(x: FloatM): ...

# to inspect annotations at runtime in another module:
from typing import get_type_hints
import isq

for param, hint in get_type_hints(
    foo,
    include_extras=True,
    localns={"isq": isq}  # add the location of your custom definitions (if any)
).items():
    print(f"`{param}`: {hint.__metadata__[0]}")
# `x`: meter
```
This makes sure that your code doesn't fail with `ImportError` if downstream
users decide not to install `your_project[typing]`.

## Tutorial: Utilities

So far, we have covered usecases for code documentation,.

Units are **immutable expression trees** and `isq` provides some runtime
utilities to *transform* the expression tree.

### Simplification

The `isq.simplify` function canonicalises it into a flat form:

```pycon
>>> from isq.usc import PSI
>>> print(PSI)
psi
- psi = lbf · inch⁻²
  - lbf = pound · 9.80665 · (meter · second⁻²)
    - pound = 0.45359237 · kilogram
  - inch = 1/12 · foot
    - foot = 0.3048 · meter
>>> from isq import simplify, dimension
>>> print(simplify(PSI))
0.45359237 · 9.80665 · (1/12)⁻² · 0.3048⁻² · (kilogram · meter⁻¹ · second⁻²)
>>> print(dimension(simplify(PSI)))
L⁻¹ · M · T⁻²
```
Note that the final scaling factor is not eagerly evaluated. This enables you to
choose between approximate and exact arithmetic (useful for financial
applications).

### Unit conversion

The `convert` function creates a callable that allow you to convert between
compatible units. Under the hood, it uses `simplify` to check dimensions and
computes the conversion factors *once*:

```pycon
>>> from isq import M, S, MIN, convert
>>> from isq.usc import FT
>>> fpm_to_mps = convert(FT * MIN**-1, M * S**-1)
>>> fpm_to_mps
Converter(scale=0.00508)
>>> fpm_to_mps(7200.0)
36.576
>>> convert(M, FT, exact=True)(11000)
Fraction(13750000, 381)
>>> convert(FT * MIN**-1, M * S**-2)  # velocity -> acceleration fails
isq._core.DimensionMismatchError: cannot convert from `foot · minute⁻¹
- foot = 0.3048 · meter
- minute = 60 · second` to `meter · second⁻²`.
= help: expected compatible dimensions, but found:
dimension of origin: `L · T⁻¹`
dimension of target: `L · T⁻²`
```
It is compatible many libraries, including using it for functional
transformations like `jax.jit`:

```pycon
>>> import numpy as np
>>> fpm_to_mps(np.linspace(-1300, 1300, 10))
array([-6.604     , -5.13644444, -3.66888889, -2.20133333, -0.73377778,
        0.73377778,  2.20133333,  3.66888889,  5.13644444,  6.604     ])
>>> import jax
>>> jax.grad(fpm_to_mps)(0.0)
Array(0.00508, dtype=float32, weak_type=True)
```
Converting between logarithmic units is also supported:

```pycon
>>> from isq import DBM, DBW, convert
>>> print(DBM)
dBm
- dBm = 10 · log₁₀(ratio[`watt` relative to `(milliwatt)`])
  - watt = joule · second⁻¹
    - joule = newton · meter
      - newton = kilogram · meter · second⁻²
>>> convert(DBW, DBM)
NonAffineConverter(scale=1.0, offset=29.999999999999996)
>>> convert(DBW, DBM)(10)
40.0
```

Note that converting between linear and logarithmic quantities are not supported.
Representing quantities like attenuation ($\text{dB}\text{ m}^{-1}$)
is permitted, but conversion of them is not yet implemented.

### Formatting

The `isq.fmt` function (called by `__format__` of expressions) by default
uses a `isq.BasicFormatter(verbose=True)`, but also supports customisation.
To use shorter symbols for example:

```pycon
>>> from isq import N, fmt, BasicFormatter
>>> f"{N}" == fmt(N, BasicFormatter(verbose=True))
True
>>> print(fmt(N, BasicFormatter(
...     verbose=True,
...     overrides={  # alias names
...         "newton": "N",
...         "kilogram": "kg",
...         "meter": "m",
...         "second": "s"
...     },
... )))
N
- N = kg · m · s⁻²
```

Internally, the basic formatter uses `isq.Visitor` to traverse each node in
post-order. You can pass in your own formatter as long as it adheres to the
`isq.Formatter` protocol.

A $\LaTeX$ formatter is WIP.

## Tutorial: Creating your own units and quantity kinds

We follow the code-as-data principle: creating units and quantity kinds can be
done effortlessly with pure Python:

```pycon
>>> from fractions import Fraction
>>> import isq
>>> SMOOT = ((5 + Fraction(7, 12)) * isq.usc.FT).alias("smoot")
>>> print(SMOOT)
smoot
- smoot = 67/12 · foot
  - foot = 0.3048 · meter
>>> print((SMOOT**-1 * isq.M * SMOOT * isq.M**-1)**2)
(smoot⁻¹ · meter · smoot · meter⁻¹)²
- smoot = 67/12 · foot
  - foot = 0.3048 · meter
```

Note that expressions are represented exactly in the order you define it:
no attempt is made to distribute exponents or combine terms unless you
[instruct it to](#simplification).

___

As explored earlier, units alone are insufficient to describe a quantity kind.
Consider we might want to represent:

| Common Units                             | Possible Quantity Kinds                                                                                                      |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| $\text{m}$, $\text{ft}$, $\text{in}$...  | *geopotential altitude* / *geometric altitude* / *wingspan* / *chord length* / *radius* / *thickness* / *wavelength*         |
| $\text{m}\text{ s}^{-1}$, $\text{kt}$... | *indicated* / *true* / *ground* speed                                                                                        |
| $\text{J}$, $\text{Btu}$                 | *internal* / *kinetic* / *potential* / *enthalpy* / *Gibbs free* energy / *work done* / *heat* / *moment of force*           |
| $\text{W}$, $\text{kWh}$                 | *instantaneous* / *RMS* / *peak-to-peak* / *time-averaged* power                                                             |
| $\text{mol}$                             | amount of *hydrogen* / *oxygen* / *(some arbitrary compound)*                                                                |
| $\text{USD}$, $\text{EUR}$...            | *nominal* / *real*, *capex* / *opex*                                                                                         |
| -                                        | radians / aspect ratio / Reynolds number <of some *characteristic length*\> / coefficient of drag (zero-lift / lift-induced) |

And that particular quantity kind may also refer to a specific:

- *inertial* / *body* / *stability* reference frame
- *x* / *y* / *z* direction
- temperature / pressure at location *A* / *B* / *C*...

#### Tags

`isq` allows you to *constrain* an existing unit with arbitrary *tags* using the
`[]` operator:

```pycon
>>> import isq
>>> MOL_H2_L = isq.MOL["H_2", "liquid"]
>>> MOL_O2_G = isq.MOL["O_2", "gas"]
>>> print(MOL_H2_L * MOL_O2_G**-1)  # does not reduce to dimensionless!
mole['H_2', 'liquid'] · (mole['O_2', 'gas'])⁻¹
```

You can use any [hashable object](https://docs.python.org/3/reference/datamodel.html#object.__hash__)
including strings, frozen dataclasses, or even `isq` units itself!
This is helpful when you want to represent something awkward like
*Reynolds number* with *characteristic length* = *chord length*.

`isq` provides two important tags, `Delta` and `OriginAt`:

```pycon
>>> import isq
>>> print(isq.K[isq.DELTA])  # finite interval/difference in temperature
kelvin[Δ]
>>> print(isq.J[isq.INEXACT_DIFFERENTIAL, "heat"])  # "small change"
joule['inexact differential', 'heat']
- joule = newton · meter
  - newton = kilogram · meter · second⁻²
>>> print(isq.M[isq.OriginAt("ground level")])  # elevation varies
meter[relative to `'ground level'`]
>>> print(isq.K[isq.DELTA, isq.OriginAt(isq.Quantity(130, K))])
kelvin[Δ, relative to `130 · kelvin`]
>>> print(isq.DBU)
dBu
- dBu = 20 · log₁₀(ratio[`volt` relative to `0.6¹⸍² · volt`])
  - volt = watt · ampere⁻¹
    - watt = joule · second⁻¹
      - joule = newton · meter
        - newton = kilogram · meter · second⁻²
```

#### Quantity Kinds

The `Tagged` class is useful, but it forces downstream users to use a specific
unit system.

Instead, use the more generic `isq.QtyKind`, a factory that produces `isq.Tagged`:

```pycon
>>> import isq
>>> DIAMETER_PIPE = isq.QtyKind(unit_si_coherent=isq.M, tags=("diameter", "pipe"))
>>> print(DIAMETER_PIPE(isq.M))
meter['diameter', 'pipe']
>>> print(DIAMETER_PIPE(isq.usc.IN))
inch['diameter', 'pipe']
- inch = 1/12 · foot
  - foot = 0.3048 · meter
>>> print(DIAMETER_PIPE(isq.usc.LB))
isq._core.UnitKindMismatchError: cannot create tagged unit for kind `('diameter', 'pipe')` with unit `pound
- pound = 0.45359237 · kilogram`.
expected dimension of kind: `L` (`meter`)
   found dimension of unit: `M` (`pound
- pound = 0.45359237 · kilogram`)
```

Users can now select the unit system they prefer, while ensuring the dimensions are correct.
