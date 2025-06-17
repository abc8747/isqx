!!! note
    Unlike libraries like `pint` which tie units to an object and use operator
    overloading to check dimension homogeneity at runtime, the goal of this
    library is to simply provide objects for use in `Annotated[T, x]` type
    hints and documentation.

Default re-exports:

- [`isq.core`][]: All logic for representing and converting between units.
- [`isq.si`][]: Definitions for SI base and derived units ([meters][isq.M], [kilograms][isq.KG], [newtons][isq.N], [joules][isq.J], etc.)
- [`isq.us_customary`][]: Definitions for US customary units ([feet][isq.FT], [slugs][isq.SLUG], [pound force][isq.LBF] etc.)

Additional useful modules not re-exported for brevity:

- [`isq.aerospace`][]: Definitions in aerospace ([TAS][isq.aerospace.M_PERS_TAS], [CAS][isq.aerospace.M_PERS_CAS], [geopotential altitude][isq.aerospace.M_ALT_GEOP] etc.)

Important rules for composing [expressions][isq.Expr]:

| Inner `→`<br/> Outer `↓` | [isq.BaseDimension][] | [isq.BaseUnit][] | [isq.Dimensionless][] | [isq.Exp][] | [isq.Mul][] | [isq.Scaled][] | [isq.Disambiguated][] | [isq.Translated][] | [isq.Logarithmic][] |
| :----------------------- | :-------------------: | :--------------: | :-------------------: | :---------: | :---------: | :------------: | :-------------------: | :----------------: | :-----------------: |
| [isq.Exp][]              |           ✅           |        ✅         |           ✅           |      ✅      |      ✅      |       ✅        |           ✅           |         ❌¹         |         ❌¹          |
| [isq.Mul][]              |           ✅           |        ✅         |           ✅           |      ✅      |      ✅      |       ✅        |           ✅           |         ❌¹         |         ❌¹          |
| [isq.Scaled][]           |           ✅           |        ✅         |           ✅           |      ✅      |      ✅      |       ✅        |           ✅           |         ❌¹         |         ⚠️⁵          |
| [isq.Prefix][]^          |          ❌²           |        ✅³        |          ❌²           |     ❌⁴      |     ⚠️⁴      |       ⚠️⁵       |          ⚠️⁶           |         ❌¹         |         ⚠️⁵          |
| [isq.Disambiguated][]    |           ✅           |        ✅         |           ✅           |      ✅      |      ✅      |       ✅        |          ❌⁹           |         ✅          |          ✅          |
| [isq.Translated][]       |          ❌⁷           |        ✅         |          ❌⁷           |     ❌⁷      |     ❌⁷      |       ✅        |          ⚠️⁶           |         ❌⁷         |         ❌⁷          |
| [isq.Logarithmic][]      |          ❌⁸           |        ✅         |          ❌⁸           |      ✅      |      ✅      |       ✅        |           ✅           |         ❌¹         |         ❌⁸          |

^ a [prefix][isq.Prefix] is not an expression, but a factory that produces a wrapped [isq.Scaled][].

1. [isq.Translated][] and [isq.Logarithmic][] are considered *terminal*, representing final concrete scales of measurement. They cannot be further [exponentiated][isq.Exp], [multiplied][isq.Mul], or [scaled][isq.Scaled]. for example, `℃²` is physically meaningless, as are `dBV·s` and `kilo(℃)`. operations on intervals must use the absolute reference unit (e.g., `J K⁻¹` instead of `J ℃⁻¹`).
2. prefixes like [`kilo-`][isq.KILO] or [`milli-`][isq.MILLI] can only be applied to expressions of `kind == 'unit'`, not `dimension` or `dimensionless`.
3. prefixes can be applied to any [isq.BaseUnit][] *except* for the [kilogram][isq.KG].
4. a [prefix][isq.Prefix] cannot be applied to an unnamed derived unit. `kilo * newton` is okay, but `kilo * Mul((M, S**-1))` is not.
5. [scaled][isq.Scaled] and [logarithmic][isq.Logarithmic] units can only be [prefixed][isq.Prefix] if their `allow_prefix` flag is `True`. this allows `milliliter` but forbids `kilo(foot)`.
6. the legality of wrapping a [isq.Disambiguated][] type depends on the rules for its inner reference. for example, `Prefix * Disambiguated(N, ...)` is legal because `Prefix * N` is legal.
7. a [translated][isq.Translated] unit (like [Celsius][isq.CELSIUS]) must have a [isq.BaseUnit][] (like [Kelvin][isq.K]) or a [isq.Scaled][] unit (like [Rankine][isq.R]) as its reference.
8. a [logarithmic][isq.Logarithmic] unit must be based on a linear unit with a physical dimension.
9. nesting [isq.Disambiguated][] types is forbidden. a tuple `("o2", "liquid")` should be used instead.

::: isq.core

::: isq.si
::: isq.us_customary

::: isq.aerospace