# isq

A tiny dependency-free Python library to define, manipulate, and convert physical units/dimensions.

At the current state, it merely serves to enable writing machine-readable, structured documentation.

## Key principles

- **No runtime value-wrapping**. Existing, mature unit-checking libraries like [`astropy.units`](https://docs.astropy.org/en/stable/units/index.html) uses operator overloading to encapsulate your data types in a new object (e.g. `(10 * u.newton) / (1 * u.kg)` returns a `Quantity` object). It checks units eagerly at runtime. This introduces performance overhead and friction with existing libraries that expect raw numerical inputs. Most simply resort to writing units in docstrings:
    ```py
    def acceleration(force, mass):
        """Return the acceleration (meters per second squared).

        :param force: Force, newtons.
        :param mass: Mass, kilograms.
        """
        return force / mass
    ```
    Instead, we leverage `Annotated[T, x]` to decorate existing types with [zero-cost metadata](https://peps.python.org/pep-0593/)
    ```py
    from typing import Any, Annotated
    from isq import N, KG, M, S

    def acceleration(
        force: Annotated[Any, N],
        mass: Annotated[Any, KG]
    ) -> Annotated[Any, M * S**-2]:
        ...
    ```
    This provides several benefits:
    - at runtime, the type is kept intact as `T`
    - enables powerful runtime introspection of `x` with `typing.get_type_hints()`.
    - delegates the type checking to an [future separate tool](#type-checking)
    - centralised source of truth
    - supports for documentation generators like `mkdocs` and intersphinx
- **Composability**: Units and dimensions are represented as immutable tree of nodes, much like SymPy.
    ```py
    from isq import N, KG

    # N = Mul((Exp(KG, 1), Exp(M, 1), Exp(S, -2)), name='newton')
    ACCELERATION = Mul((Exp(N, 1), Exp(KG, -1)))
    print(ACCELERATION)
    # Mul((Exp(N, 1), Exp(KG, -1)))
    ```
    Sometimes, we just want a semantically meaningful unit. Units are not aggressively simplified by default.
- **Simplification**: The `simplify()` method reduces complex nested expressions into a canonical form (product of base units raised to powers, potentially scaled).
    ```py
    from isq import N, KG, Exp, Mul

    ACCELERATION = Mul((Exp(N, 1), Exp(KG, -1)))
    print(ACCELERATION.simplify())
    # Mul((Exp(M, 1), Exp(S, -2)))
    ```
    This forms the basis for checking dimensional homogeneity.
- **Unit Conversion**: The `to()` method returns a function that allow you to convert between compatible units.
    ```py
    from isq import FT, MIN, M, S, Exp, Mul

    # FT = Scaled(M, factor=Decimal('0.3048'))
    # MIN = Scaled(S, factor=60)
    FT_PER_MIN = Mul((Exp(FT, 1), Exp(MIN, -1)))
    M_PER_S = Mul((Exp(M, 1), Exp(S, -1)))
    fpm2mps = FT_PER_MIN.to(M_PER_S)
    print(fpm2mps(1000, exact=True))  # Fraction(127, 25)
    print(fpm2mps(100.0))  # 0.508
    ```
    The function accepts any type that implements `__mul__`, making it compatible with many libraries, including numpy and `jax.jit`. `exact=True` is useful for money conversions.
- **Plug-and-play extensibility**: Create your own units without DSL, just Python classes.
    ```py
    from isq import BaseDimension, BaseUnit, Scaled, Mul, Exp, HOUR, WEEK
    from decimal import Decimal

    DIM_MONEY = BaseDimension("MONEY")
    USD = BaseUnit(DIM_MONEY, name="USD")
    HKD = Scaled(USD, factor=1 / Decimal("7.8"), name="HKD")
    USD_PER_HR = Mul((Exp(USD, 1), Exp(HOUR, -1)))
    HKD_PER_YEAR = Mul((Exp(HKD, 1), Exp(WEEK, -1)))
    print(USD_PER_HR.to(HKD_PER_WEEK)(13))  # 888872.4
    ```
- First class support for non-SI units.

## TODOs

- enable intuitive construction like `M * S**-1` directly producing new `Expr` objects (impl `__mul__`, `__truediv__`, `__pow__` for `Expr`)
- allow `simplify(keep_named=True)` to preserve user-defined `Scaled` units (e.g. keep `psi` rather than always reducing down to `lbf in**-2` or even further)
- "geopotential altitude" and "geometric altitude" both have the same dimension but have different semantic meaning. develop the `Disambiguation` class.
- support for prefixes (e.g. `KILO`)
- support for tricky affine units (e.g., farenheit, celsius)
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

## Installation

```sh
# with pip
pip install https://github.com/cathaypacific8747/isq
# with uv
uv add https://github.com/cathaypacific8747/isq
```
