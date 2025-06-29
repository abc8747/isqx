# isq

A tiny dependency-free Python library to define, manipulate, and convert units/dimensions based on the International System of Quantities.

Unlike mature unit-checking libraries like [`astropy.units`](https://github.com/astropy/astropy) which encapsulate numerical values in a new object (a `numpy.ndarray * unit` becomes a `Quantity`), this library **does not perform runtime dimensional homogenity checks**.

At the current state, it merely serves to enable writing machine-readable, structured documentation.

## Key principles

- Inspired by libraries like [Pydantic](https://github.com/pydantic/pydantic) and [annotated-types](https://github.com/annotated-types/annotated-types), this library offers metadata objects that can be used in `typing.Annotated[T, x]`:
    ```py
    from typing import Any, Annotated
    from isq import N, KG, M, S

    def acceleration(
        force: Annotated[Any, N],
        mass: Annotated[Any, KG]
    ) -> Annotated[Any, M * S**-2]:
        ...
    ```
    - the type is kept intact as `T`, with zero runtime overhead (see [PEP 593](https://typing.python.org/en/latest/spec/qualifiers.html#annotated))
    - powerful runtime introspection of `x` with `typing.get_type_hints()`.
    - delegates the type checking to a [separate tool](#type-checking)
    - centralised source of truth
    - supports documentation generators like `mkdocs` and intersphinx
    - incremental, optional adoption
    - use in `dataclass`, `TypedDict`, `NamedTuple`...
- Units and dimensions are represented as an immutable expression tree, much like SymPy. The `simplify` function folds it into a flat, canonical form.
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
    ```
    The final factor is lazily evaluated, enabling exact arithmetic for financial applications.
- The `convert` function returns a callable that allow you to convert between compatible units.
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
    ```
    The callable is compatible with many libraries, including `numpy` and `jax.jit`.
- Define your own units without DSL.
    ```pycon
    >>> from fractions import Fraction
    >>> from isq import M, convert
    >>> from isq.us_customary import FT
    >>> SMOOT = ((5 + Fraction(7, 12)) * FT).alias("smoot")
    >>> print(SMOOT)
    smoot
    - smoot = 67/12 · foot
      - foot = 0.3048 · meter
    >>> convert(SMOOT, M, exact=True)(Fraction("364.4"))
    Fraction(7751699, 12500)
    ```
- Different quantities often share the same physical dimension but are semantically distinct. For example:
    - geopotential vs geometric altitude (ft), true vs ground speed (knots), $V_\text{rms}$ vs $V_\text{pp}$
    - inertial vs body vs wind reference frames
    - Reynolds number of pipe diameter vs. chord
    - $\Delta U = Q - W$, kinetic vs potential vs enthalpy vs Gibbs free energy (joules)
    - nominal vs real, capex vs opex (money)
    - force in the x, y and z directions (newtons)

    Create a *kind of quantity* which can materialise to a `Tagged` class:
    ```pycon
    >>> from isq.aerospace import TAS, IAS
    >>> TAS
    QtyKind(unit_si=..., context=('airspeed', 'true'))
    >>> IAS
    QtyKind(unit_si=..., context=('airspeed', 'indicated'))
    >>> from isq.us_customary import KNOT
    >>> TAS[KNOT]
    Tagged(reference=..., context=('airspeed', 'true'))
    >>> from isq import simplify, convert, M, S
    >>> simplify(TAS[KNOT] / IAS[KNOT]) # does not reduce to dimensionless!
    Mul(terms=(Exp(Tagged(...), -1), Tagged(...)))
    >>> convert(TAS[KNOT], TAS[M * S**-1]) # only works for matching context
    Converter(scale=0.5144444444444445, offset=0.0)
    >>> convert(IAS[KNOT], TAS[KNOT]) # fails!
    isq.core.DimensionMismatchError: ...
    ```

## TODOs

- support more string representations (e.g. LaTeX)
  - compile LaTeX to SVG and manipulate symbols
- mindmap

### Type checking

Right now, using `Annotated[T, x]` without actually checking `x` is just glorified comments. For this library to be truly useful, it should perform static analysis to avoid unit mismatches. Such a compile-time tool is not yet implemented.

One possible path is to use tracer objects that record operations just-in-time, and error out when dimensions do not match. But this is extremely difficult for several reasons:

- it is common for a `numpy.NDArray` or `polars.DataFrame` to represent different units for each row/column.
  - determining the units for the matmul between two arrays is very difficult.
- interfacing with complex function transformations like `jax.grad(f)(x)` and `numpy.fft.fft` require significant maintenance burden.

Moving forward, the first MVP should start with simple function boundary checks, *only* at points where data crosses a declared "unit boundary" (argument passing, return statements). This alone would already cover most usecases.

Intra-expression errors (e.g. `distance_m + time_s`) are significantly more difficult to deal with and come much later.

Such a tool will be released as an optional feature, separate from the core library.

## Installation

```sh
# with pip
pip install https://github.com/cathaypacific8747/isq
# with uv
uv add https://github.com/cathaypacific8747/isq
```
