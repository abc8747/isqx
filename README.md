# isq

A tiny dependency-free Python library to define, manipulate, and convert physical units/dimensions.

Unlike mature unit-checking libraries like [`astropy.units`](https://github.com/astropy/astropy) which encapsulate your data types in a new object (a `numpy.ndarray` becomes a `Quantity`), this library **does not perform runtime dimensional homogenity checks**.

At the current state, it merely serves to enable writing machine-readable, structured documentation.

## Key principles

- Inspired by modern data validation libraries like [Pydantic](https://github.com/pydantic/pydantic), this library offers metadata objects that can be used in `typing.Annotated[T, x]`:
    ```py
    from typing import Any, Annotated
    from isq import N, KG, M, S, Mul, Exp

    def acceleration(
        force: Annotated[Any, N],
        mass: Annotated[Any, KG]
    ) -> Annotated[Any, Mul((M, Exp(S, -2)))]:
        ...
    ```
    Benefits:
    - the type is kept intact as `T`, with zero runtime overhead (see [PEP 593](https://peps.python.org/pep-0593/))
    - enables powerful runtime introspection of `x` with `typing.get_type_hints()`.
    - delegates the type checking to an [separate tool](#type-checking)
    - centralised source of truth
    - supports documentation generators like `mkdocs` and intersphinx
    - incremental, optional adoption
    - use in `dataclass`, `TypedDict`, `NamedTuple`...
- Units and dimensions are represented as an immutable expression tree, much like SymPy.
    ```py
    from isq import N, KG, Mul, Exp

    # N = Alias(Mul((KG, M, Exp(S, -2))), name="newton")
    ACCELERATION = Mul((N, Exp(KG, -1)))
    print(ACCELERATION) # Mul((N, Exp(KG, -1)))
    print(ACCELERATION.simplify()) # Mul((M, Exp(S, -2)))
    ```
    Ordering is preserved. The `simplify()` method reduces the complex nested tree into a flat canonical form (product of base units raised to powers, potentially scaled).
- The `to()` method returns a callable that allow you to convert between compatible units.
    ```py
    from isq import FT, MIN, M, S, Mul, Exp

    # FT = Scaled(M, factor=Decimal("0.3048"))
    # MIN = Scaled(S, factor=60)
    FT_PER_MIN = Mul((FT, Exp(MIN, -1)))
    M_PER_S = Mul((M, Exp(S, -1)))
    fpm2mps = FT_PER_MIN.to(M_PER_S)
    print(fpm2mps(100.0))  # 0.508
    print(FT_PER_MIN.to(M_PER_S, exact=True)(1000))  # Fraction(127, 25)
    ```
    The callable is compatible with many libraries, including `numpy` and `jax.jit`. Exact arithmetic is supported, useful for financial applications.
- Define your own units without DSL.
    ```py
    from fractions import Fraction
    from isq import FT, M, Scaled

    SMOOT = Scaled(FT, factor=5 + Fraction(7, 12))
    print(SMOOT.to(M, exact=True)(Fraction("364.4")))  # 7751699/12500
    ```
- Different quantities often share the same physical dimension but are semantically distinct. For example:
    - geopotential vs geometric altitude (ft)
    - true vs ground speed (knots)
    - inertial vs body vs wind reference frames
    - $\Delta U = Q - W$, kinetic vs potential vs enthalpy vs Gibbs free energy (joules)
    - nominal vs real, capex vs opex (money)
    - force in the x, y and z directions (newtons)

    Create a *kind of quantity* which can materialise to a `Tagged` class:
    ```py
    from isq import QtyKind, Mul, Exp, M_PERS, KNOT

    GS = QtyKind(M_PERS, context=("airspeed", "ground"))
    TAS = QtyKind(M_PERS, context=("airspeed", "true"))
    
    M_PERS_GS = GS[M_PERS] # Tagged(M_PERS, context=("airspeed", "ground"))
    KNOT_GS = GS[KNOT] # Tagged(KNOT, context=("airspeed", "ground"))

    Mul((TAS[KNOT], Exp(GS[KNOT], -1))).simplify() # NOT dimensionless.
    # TAS[KNOT].to(GS[KNOT])  # errors due to contextual mismatch
    ```

## TODOs

- enable intuitive construction like `M * S**-1` directly producing new `Expr` objects (impl `__mul__`, `__truediv__`, `__pow__`, `.alias()` for `Expr`)
- convert `Expr` objects to various string representations (`siunitx`, LaTeX, ASCII, etc).
- potentially, create a `mkdocs` plugin that serialises them

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
