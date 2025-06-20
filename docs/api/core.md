!!! note
    Unlike libraries like `pint` which tie units to an object and use operator
    overloading to check dimension homogeneity at runtime, the goal of this
    library is to simply provide objects for use in `Annotated[T, x]` type
    hints and documentation.

Default re-exports:

- [`isq.core`][]: All logic for representing and converting between units.
- [`isq.si`][]: Definitions for SI base and derived units ([meters][isq.M], [kilograms][isq.KG], [newtons][isq.N], [joules][isq.J], etc.)
- [`isq.us_customary`][]: Definitions for U.S. customary and British imperial units ([feet][isq.FT], [slugs][isq.SLUG], [pound force][isq.LBF] etc.)

Additional useful modules not re-exported for brevity:

- [`isq.aerospace`][]: Definitions in aerospace ([TAS][isq.aerospace.TAS], [CAS][isq.aerospace.CAS], [geopotential altitude][isq.aerospace.ALT_GEOP] etc.)

Restrictions for composing [expressions][isq.Expr]:

| Inner `→`<br/> Outer `↓` | [isq.BaseDimension][] | [isq.BaseUnit][] | [isq.Dimensionless][] | [isq.Exp][] | [isq.Mul][] | [isq.Scaled][] | [isq.Alias][] | [isq.Tagged][] | [isq.Translated][] | [isq.Logarithmic][] |
| :----------------------- | :-------------------: | :--------------: | :-------------------: | :---------: | :---------: | :------------: | :-----------: | :------------: | :----------------: | :-----------------: |
| [isq.Exp][]              |           ✅           |        ✅         |           ✅           |      ✅      |      ✅      |       ✅        |       ✅       |       ✅        |         ❌¹         |         ❌¹          |
| [isq.Mul][]              |           ✅           |        ✅         |           ✅           |      ✅      |      ✅      |       ✅        |       ✅       |       ✅        |         ❌¹         |         ❌¹          |
| [isq.Scaled][]           |           ✅           |        ✅         |           ✅           |      ✅      |      ✅      |       ✅        |       ✅       |       ✅        |         ❌¹         |         ⚠️⁵          |
| [isq.Prefix][]^          |          ❌²           |        ✅³        |          ❌²           |     ❌⁴      |     ❌⁴      |       ❌⁴       |      ✅⁶       |       ⚠️⁷       |         ❌¹         |         ⚠️⁵          |
| [isq.Alias][]            |          ❌⁸           |        ❌⁸        |          ❌⁸           |      ✅      |      ✅      |       ✅        |      ❌⁹       |       ✅        |         ❌¹         |          ✅          |
| [isq.Tagged][]           |           ✅           |        ✅         |           ✅           |      ✅      |      ✅      |       ✅        |       ✅       |      ❌¹⁰       |         ✅          |          ✅          |
| [isq.Translated][]       |          ❌¹¹          |        ✅         |          ❌¹¹          |     ❌¹¹     |     ❌¹¹     |       ✅        |       ✅       |       ⚠️⁷       |         ❌¹         |         ❌¹          |
| [isq.Logarithmic][]      |          ❌¹²          |        ✅         |          ❌¹²          |      ✅      |      ✅      |       ✅        |       ✅       |       ✅        |         ❌¹         |         ❌¹²         |

^ a [prefix][isq.Prefix] is not an expression, but a factory that produces an [aliased][isq.Alias] scaled unit.

1.  [isq.Translated][] and [isq.Logarithmic][] are considered *terminal* and cannot be further composed with other expressions, except for being [tagged][isq.Tagged]. for example, `℃²` is physically meaningless, as are `dBV·s` and `kilo(℃)`. operations on intervals must use the absolute reference unit (e.g., `J K⁻¹` instead of `J ℃⁻¹`).
2.  prefixes like [`kilo-`][isq.KILO] or [`milli-`][isq.MILLI] can only be applied to units, not [dimensionless numbers][isq.Dimensionless] or [dimensions][isq.BaseDimension].
3.  prefixes can be applied to any [isq.BaseUnit][] *except* for the [kilogram][isq.KG].
4.  a [prefix][isq.Prefix] must be applied to a *named* unit, which is either a [isq.BaseUnit][] or an [isq.Alias][]. it cannot be applied to structural expressions like `Exp`, `Mul`, or `Scaled` directly.
5.  a [logarithmic][isq.Logarithmic] unit can only be [prefixed][isq.Prefix] if its `allow_prefix` flag is `True`.
6.  a [prefix][isq.Prefix] can be applied to an [isq.Alias][] if its `allow_prefix` flag is `True` (e.g., `kilo * N`).
7.  the legality of wrapping a [isq.Tagged][] type depends on the rules for its inner reference. for example, `Prefix * Tagged(N, ...)` is legal because `Prefix * N` is legal.
8.  an [isq.Alias][] must wrap a structural expression (`Exp`, `Mul`, `Scaled`) or a `Logarithmic` unit. it cannot wrap fundamental types like `BaseUnit` or `Dimensionless`.
9.  nesting [isq.Alias][] types is forbidden.
10. nesting [isq.Tagged][] types is forbidden. a tuple `("o2", "liquid")` should be used for the context instead.
11. a [translated][isq.Translated] unit (like [Celsius][isq.CELSIUS]) must have a [isq.BaseUnit][] or a [isq.Scaled][] unit (like [Rankine][isq.R]) as its reference.
12. a [logarithmic][isq.Logarithmic] unit must be based on a linear unit with a physical dimension. it cannot be based on a dimensionless number.

::: isq.core

::: isq.si
::: isq.us_customary