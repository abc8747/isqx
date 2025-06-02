# isq

A tiny Python library to define, manipulate, and convert physical units and dimensions.

## Key principles

- **Composability**: Units and dimensions are represented as immutable tree of nodes.
    ```py
    from isq import N, J

    # N = Mul((Exp(KG, 1), Exp(M, 1), Exp(S, -2)), name='newton')
    # J = Mul((Exp(N, 1), Exp(M, 1)), name='joule')
    ```
    The ordering and nesting is intentionally preserved for serialisation.
- **Simplification**: The `simplify()` method reduces complex nested expressions into a canonical form (product of base units raised to powers, potentially scaled).
    ```py
    from isq import N, J, Exp, Mul

    DISPLACEMENT = Mul((Exp(J, 1), Exp(N, -1)))  # W = F⋅s
    print(DISPLACEMENT.simplify()) 
    # BaseUnit(_dimension=BaseDimension(name='L'), name='meter')
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
- **Plug-and-play extensibility**: Create your own units without DSL.
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

## Installation

```sh
# with pip
pip install https://github.com/cathaypacific8747/isq
# with uv
uv add https://github.com/cathaypacific8747/isq
```

## TODO

- enable intuitive construction like `M * S**-1` directly producing new `Expr` objects.
- allow `simplify(keep_scaled=True)` to preserve user-defined `Scaled` units (e.g. keep `FT` rather than always reducing down to `M`)
- develop the `Disambiguation` class to allow tagging units with semantic meaning (e.g., `M` as "geopotential altitude" vs. M as "geometric altitude").
- support for affine units (e.g., farenheit, celsius)
- convert `Expr` objects to various string representations (`siunitx`, LaTeX, ASCII, etc).
- ultimate goal: enable static type checking of unit correctness using `typing.Annotated`.

