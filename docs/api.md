A dependency-free library for representing physical units.

!!! note
    Unlike libraries like `pint` which tie units to an object and use operator
    overloading to check dimension homogeneity at runtime, the goal of this
    library is to simply provide objects for use in `Annotated[T, x]` type
    hints and documentation.

Default re-exports:

- [`isq.core`][]: All logic for representing and converting between units.
- [`isq.si`][]: Definitions for SI base and derived units (m, N, J, etc.)
- [`isq.us_customary`][]: Definitions for US customary units (ft, mi, lbf etc.)

Additional useful modules not re-exported for brevity:

- [isq.aerospace][]: Definitions in aerospace (TAS, CAS, geopotential alt etc.)

::: isq.core

::: isq.si
::: isq.us_customary

::: isq.aerospace