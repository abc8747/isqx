!!! note
    Unlike libraries like `pint` which tie units to an object and use operator
    overloading to check dimension homogeneity at runtime, the goal of this
    library is to simply provide objects for use in `Annotated[T, x]` type
    hints and documentation.

Default top level `isq` re-exports:

- [`isq.core`][]: Expression tree, simplification, conversion.
- [`isq.fmt`][]: Serialisation
- [`isq.si`][]: Definitions for SI base and derived units ([meters][isq.M], [kilograms][isq.KG], [newtons][isq.N], [joules][isq.J], etc.)

Additional useful modules not re-exported for brevity:

- [`isq.us_customary`][]: Definitions for U.S. customary and British imperial units ([feet][isq.us_customary.FT], [slugs][isq.us_customary.SLUG], [pound force][isq.us_customary.LBF] etc.)
- [`isq.aerospace`][]: Quantity kinds in aerospace ([TAS][isq.aerospace.TAS], [CAS][isq.aerospace.CAS], [geopotential altitude][isq.aerospace.ALT_GEOP] etc.)

Restrictions for composing [expressions][isq.Expr] with examples:

| Inner `→`<br/> Outer `↓` |       [isq.BaseDimension][]        |         [isq.BaseUnit][]          |        [isq.Dimensionless][]         |              [isq.Exp][]              |                             [isq.Mul][]                              |             [isq.Scaled][]              |        [isq.Aliased][]         |                              [isq.Tagged][]                               |             [isq.Translated][]             |              [isq.Log][]               |
| :----------------------- | :--------------------------------: | :-------------------------------: | :----------------------------------: | :-----------------------------------: | :------------------------------------------------------------------: | :-------------------------------------: | :----------------------------: | :-----------------------------------------------------------------------: | :----------------------------------------: | :------------------------------------: |
| [isq.Exp][]              |         ✅<br/>$\text{L}^2$         |        ✅<br/>$\text{m}^2$         |       ✅<br/>$\text{Re}^{1/5}$        |        ✅<br/>$(\text{m}^2)^2$         |                ✅<br/>$(\text{m}\cdot\text{s}^{-1})^2$                |           ✅<br/>$\text{ft}^2$           |               ✅                |                                     ✅                                     |         ❌¹<br/>$\degree\text{C}^2$         |         ❌¹³<br/>$\text{dBV}^2$         |
| [isq.Mul][]              | ✅<br/>$\text{L}\cdot\text{T}^{-2}$ |   ✅<br/>$\text{N}\cdot\text{m}$   | ✅<br/>$\text{rad}\cdot\text{s}^{-1}$ |  ✅<br/>$\text{m}\cdot\text{s}^{-2}$   | ✅<br/>$(\text{kg}\cdot\text{m}\cdot\text{s}^{-1})\cdot\text{s}^{-1}$ |    ✅<br/>$\text{lbf}\cdot\text{ft}$     | ✅<br/>$\text{N}\cdot\text{m}$  |            ✅<br/>$\text{m}_\text{geometric}\cdot\text{s}^{-2}$            | ❌¹<br/>$\text{J}\cdot\degree\text{C}^{-1}$ | ⚠️¹⁴<br/>$\text{dBV}\cdot\text{s}^{-1}$ |
| [isq.Scaled][]           |                 ❌                  |     ✅<br/>$1000\cdot\text{m}$     |                  ❌                   |      ✅<br/>$100\cdot\text{m}^2$       |             ✅<br/>$3.6\cdot(\text{m}\cdot\text{s}^{-1})$             |      ✅<br/>$\frac{1}{12}\text{ft}$      |      ✅<br/>$10^3\text{J}$      | ✅<br/>$\text{ft}_\text{geometric} = 0.3048\cdot\text{m}_\text{geometric}$ |      ❌¹<br/>$1.8\cdot\degree\text{C}$      |        ✅<br/>$10\cdot \text{B}$        |
| [isq.Prefix][]^          |                 ❌²                 |        ✅³<br/>$\text{km}$         |  ❌²<br/>$\text{kilo}\cdot\text{Re}$  |  ❌⁴<br/>$\text{kilo}\cdot\text{m}^2$  |        ❌⁴<br/>$\text{kilo}\cdot(\text{m}\cdot\text{s}^{-1})$         |   ❌⁴<br/>$\text{kilo}\cdot\text{ft}$    |       ✅⁶<br/>$\text{kJ}$       |                    ⚠️⁷<br/>$\text{km}_\text{geometric}$                    |  ❌¹<br/>$\text{kilo}\cdot\degree\text{C}$  |          ✅⁵<br/>$\text{mNp}$           |
| [isq.Aliased][]          |                 ❌⁸                 |                ❌⁸                 |                  ❌⁸                  |   ✅<br/>$\text{sqft} = \text{ft}^2$   |                ✅<br/>$\text{J}=\text{N}\cdot\text{m}$                | ✅<br/>$\text{ft} = 0.3048\cdot\text{m}$ |               ❌⁹               |                      ✅<br/>$\text{N}_\text{thrust}$                       |                     ❌¹                     |       ✅<br/>$\text{B} = \log...$       |
| [isq.Tagged][]           | ✅<br/>$\text{L}_\text{geometric}$  | ✅<br/>$\text{m}_\text{geometric}$ |    ✅<br/>$\text{Re}_\text{chord}$    | ✅<br/>$({\text{m}^2})_\text{surface}$ |            ✅<br/>$(\text{N}\cdot\text{m})_\text{torque}$             |   ✅<br/>$\text{ft}_\text{geometric}$    | ✅<br/>$\text{N}_\text{thrust}$ |                                    ❌¹⁰                                    |  ✅<br/>$(\degree\text{C})_\text{surface}$  |          ✅<br/>$\text{dB(A)}$          |
| [isq.Translated][]       |      ❌¹¹<br/>$\text{L} + 13$       |     ✅<br/>$\text{K} - 273.15$     |       ❌¹¹<br/>$\text{Re} - 13$       |       ❌¹¹<br/>$\text{m}^2 + 13$       |                ❌¹¹<br/>$(\text{N}\cdot\text{m}) + 13$                |    ✅<br/>$\degree\text{R} - 459.67$     |               ⚠️                |                   ✅<br/>$\text{K}_\text{ambient} + 13$                    |       ❌¹<br/>$\degree\text{C} + 13$        |        ❌¹<br/>$\text{dBV} + 10$        |
| [isq.Log][]              |                ❌¹²                 |                ❌¹²                |           ✅<br/>$\text{B}$           |      ❌¹²<br/>$\log(\text{m}^2)$       |    ❌¹²<br/>$\log(\text{W}\cdot\text{m}^{-2}\cdot\text{Hz}^{-1})$     |        ❌¹²<br/>$\log(\text{mW})$        |    ❌¹²<br/>$\log(\text{W})$    |                   ✅<br/>$\log(\text{ratio}_\text{V/V})$                   |       ❌¹<br/>$\log(\degree\text{C})$       |       ❌¹²<br/>$\log(\text{dBV})$       |

    
^ a [prefix][isq.Prefix] is not an expression, but a factory that produces an [aliased][isq.Aliased] scaled unit.

1.  [isq.Translated][] is considered *terminal* and cannot be further composed with other expressions, except for being [tagged][isq.Tagged]. for example, `℃²` is physically meaningless, as are `kilo(℃)`. operations on intervals must use the absolute reference unit (e.g., `J K⁻¹` instead of `J ℃⁻¹`).
2.  prefixes like [`kilo-`][isq.KILO] or [`milli-`][isq.MILLI] can only be applied to units, not [dimensionless numbers][isq.Dimensionless] or [dimensions][isq.BaseDimension].
3.  prefixes can be applied to any [isq.BaseUnit][] *except* for the [kilogram][isq.KG].
4.  a [prefix][isq.Prefix] must be applied to a *named* unit, which is either a [isq.BaseUnit][] or an [isq.Aliased][]. it cannot be applied to structural expressions like `Exp`, `Mul`, or `Scaled` directly.
5.  a [logarithmic][isq.Log] can only be [prefixed][isq.Prefix] if its `allow_prefix` flag is `True`.
6.  a [prefix][isq.Prefix] can be applied to an [isq.Aliased][] if its `allow_prefix` flag is `True` (e.g., `kilo * N`).
7.  the legality of wrapping a [isq.Tagged][] type depends on the rules for its inner reference. for example, `Prefix * Tagged(N, ...)` is legal because `Prefix * N` is legal.
8.  an [isq.Aliased][] must wrap a structural expression (`Exp`, `Mul`, `Scaled`). it cannot wrap fundamental, terminal or aliased expressions.
9.  nesting [isq.Aliased][] types is forbidden.
10. nesting [isq.Tagged][] types is forbidden. a tuple `("o2", "liquid")` should be used for the context instead.
11. a [translated][isq.Translated] unit (like [Celsius][isq.CELSIUS]) must have a [isq.BaseUnit][] or a [isq.Scaled][] unit (like [Rankine][isq.us_customary.R]) as its reference.
12. a [logarithmic][isq.Log] expression must wrap a [dimensionless][isq.Dimensionless] expression. it cannot wrap another logarithmic expression or an expression with a physical dimension.
13. a [logarithmic][isq.Log] expression is considered terminal and cannot be exponentiated.
14. a product can contain at most one [logarithmic][isq.Log] expression. this is to allow common units like `dB/m` or `dB/Hz` while forbidding physically meaningless compositions like `dB·m` or `dB²`.

::: isq.core
::: isq.fmt