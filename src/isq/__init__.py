"""
A system for representing physical units, contains a selection of commonly
used SI and US Customary Units.

Unlike libraries like `pint` which use runtime unit-aware number types,
we do not seek to "wrap" numerical values with their units.
It is common for different rows in a matrix to represent different quantities,
making it very difficult to annotate properly. Instead, this library treats
units as metadata for use in static analysis tools and documentation.

[1] The International System of Units (SI): Text in English (updated in 2024),
    9th edition 2019, V3.01 August 2024. Sèvres Cedex BIPM 2024, 2024.
    Available: https://www.bipm.org/documents/20126/41483022/SI-Brochure-9-EN.pdf

[2] C. C2, "C2: Commission on Symbols, Units, Nomenclature, Atomic Masses and
    Fundamental Constants - IUPAP: The International Union of Pure and Applied
    Physics," Mar. 04, 2021. Available: https://archive2.iupap.org/wp-content/uploads/2014/05/A4.pdf

[3] "NIST Handbook 44 - 2024 - Appendix C. General Tables of Units of
    Measurement," NIST, Available: https://www.nist.gov/document/nist-handbook-44-2024-appendix-c-pdf
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Callable, Literal, Union

from typing_extensions import TypeAlias

_ExpressionKind: TypeAlias = Literal["dimensionless", "unit", "dimension"]


class Expr:
    """Base class that represents a unit or dimension expression."""

    @property
    def kind(self) -> _ExpressionKind:
        if isinstance(self, Dimensionless):
            return "dimensionless"
        elif isinstance(self, BaseUnit):
            return "unit"
        elif isinstance(self, BaseDimension):
            return "dimension"
        elif isinstance(self, Exp):
            return self.base.kind
        elif isinstance(self, Mul):
            # all terms have a consistent underlying kind (unit/dimension)
            for term in self.terms:
                term_kind = term.base.kind
                if term_kind != "dimensionless":
                    return term_kind
            return "dimensionless"
        elif isinstance(self, Scaled):
            return self.reference.kind
        else:
            raise TypeError(
                f"cannot determine kind for unknown expression type: {type(self)}"
            )


@dataclass(frozen=True)
class Dimensionless(Expr):
    name: str
    """Name for the dimensionless number, e.g. `reynolds`, `stanton`"""


@dataclass(frozen=True)
class BaseDimension(Expr):
    name: str
    """Name for the base dimension, e.g. `L`, `M`, `T`"""


@dataclass(frozen=True)
class BaseUnit(Expr):
    name: str
    """Name for the unit, e.g. `m`, `kg`, `s`"""
    dimension: BaseDimension
    """Reference to the base dimension"""


Exponent: TypeAlias = Union[int, Fraction]
"""An exponent, generally small integers, which can be positive, negative,
or a fraction, but not zero"""


@dataclass(frozen=True)
class Exp(Expr):
    """An expression raised to an exponent.
    For example, `BaseUnit("meter", Dimension("L")), 2)` is m².
    Can be recursively nested, e.g. `Exp(Exp(METER, 2), Fraction(1, 2))`
    """

    base: Expr
    """Base unit, dimension, dimensionless number or [isq.Mul][] itself."""
    exponent: Exponent
    """Exponent. Avoid using zero to represent dimensionless numbers: 
    use [isq.Dimensionless][] with a name instead."""

    def __post_init__(self) -> None:
        if self.exponent == 0:
            raise ValueError("exponent must not be zero, use `Dimensionless`")

    def simplify(self) -> Expr:
        """Flatten the tree-like structure into the simplest form."""
        base_exponent_pairs: dict[Expr, Exponent] = {}
        derived_conversions: list[tuple[Scaled, Exponent]] = []
        _insert_root_term(self, base_exponent_pairs, derived_conversions)
        return _get_canonical_expression(
            base_exponent_pairs,
            derived_conversions,
            output_name_maybe=f"expr_{hash(self)}",
        )


@dataclass(frozen=True)
class Mul(Expr):
    """Products of powers of an expression."""

    terms: tuple[Exp, ...]
    """A tuple of expressions raised to an exponent."""
    name: str | None = None
    """Name for this expression, e.g. `newton`, `joule`"""

    def __post_init__(self) -> None:
        n_terms = len(self.terms)
        if n_terms == 0:
            raise ValueError("terms must not be empty, use `Dimensionless`")
        unique_kinds = set(t.base.kind for t in self.terms) - {"dimensionless"}
        if len(unique_kinds) != 1:
            raise ValueError("terms must all be either `unit` or `dimension`")

    def simplify(self) -> Expr:
        """Flatten the tree-like structure into the simplest form."""
        base_exponent_pairs: dict[Expr, Exponent] = {}
        derived_conversions: list[tuple[Scaled, Exponent]] = []
        for term in self.terms:
            _insert_root_term(term, base_exponent_pairs, derived_conversions)
        return _get_canonical_expression(
            base_exponent_pairs,
            derived_conversions,
            output_name_maybe=self.name or f"expr_{hash(self)}",
        )


@dataclass(frozen=True)
class Scaled(Expr):
    name: str
    """Name of this unit or dimension."""
    reference: Expr
    """The unit or dimension that this unit or dimension is based on."""
    factor: float | Fraction
    """Multiplying this factor converts this value into the reference.
    For example, `1 ft = 0.3048 m`, so the factor is 0.3048."""

    def to_reference(self, value: Any) -> Any:
        """Convert a value in this unit to the reference unit."""
        return value * self.factor

    def from_reference(self, value: Any) -> Any:
        """Convert a value in the reference unit to this unit."""
        return value / self.factor

    def to(self, other: Expr) -> Callable[[Any], Any]:
        """Return a function that converts a value in this unit to another unit.
        :param other: The target unit or dimension to convert to.
        :raises RuntimeError: if the other unit is not compatible with this one.
        """
        raise NotImplementedError


def _insert_root_term(
    term: Exp,
    base_exponent_pairs_mut: dict[Expr, Exponent],
    derived_conversions_mut: list[tuple[Scaled, Exponent]],
) -> None:
    if isinstance(term.base, (BaseUnit, BaseDimension, Dimensionless)):
        base_exponent_pairs_mut.setdefault(term.base, 0)
        base_exponent_pairs_mut[term.base] += term.exponent
    elif isinstance(term.base, Mul):
        terms_distributed = tuple(
            Exp(term_inner.base, term_inner.exponent * term.exponent)
            for term_inner in term.base.terms
        )
        for term in terms_distributed:
            _insert_root_term(
                term,
                base_exponent_pairs_mut,
                derived_conversions_mut,
            )
    elif isinstance(term.base, Exp):
        term_inner = term.base
        term_distributed = Exp(
            term_inner.base, term_inner.exponent * term.exponent
        )
        _insert_root_term(
            term_distributed,
            base_exponent_pairs_mut,
            derived_conversions_mut,
        )
    elif isinstance(term.base, Scaled):
        term_derived = term.base
        derived_conversions_mut.append((term_derived, term.exponent))
        ref_expr = Exp(term_derived.reference, term.exponent)
        _insert_root_term(
            ref_expr,
            base_exponent_pairs_mut,
            derived_conversions_mut,
        )
    else:
        raise ValueError(f"unknown expression {term}")


def _get_canonical_expression(
    base_exponent_pairs: dict[Expr, Exponent],
    derived_conversions: list[tuple[Scaled, Exponent]],
    *,
    output_name_maybe: str,
) -> Expr:
    no_conversions_involved = not derived_conversions
    simplified_expr: Expr
    # remove zero exponents and ensure canonical order by names
    base_exponent_pairs_sorted = sorted(
        filter(lambda item: item[1] != 0, base_exponent_pairs.items()),
        key=lambda item: item[0].name,  # type: ignore
    )
    if not base_exponent_pairs_sorted:
        simplified_expr = Dimensionless(
            name=f"dimensionless_form_of_{output_name_maybe}"
        )
    elif len(base_exponent_pairs_sorted) == 1:
        base, exponent = base_exponent_pairs_sorted[0]
        simplified_expr = base if exponent == 1 else Exp(base, exponent)
    else:
        simplified_expr = Mul(
            tuple(
                Exp(base, exponent)
                for base, exponent in base_exponent_pairs_sorted
            ),
            name=output_name_maybe if no_conversions_involved else None,
        )
    if no_conversions_involved:
        return simplified_expr

    factor = 1.0
    for derived, exponent in derived_conversions:
        factor *= derived.factor**exponent

    return Scaled(
        name=output_name_maybe,
        reference=simplified_expr,
        factor=factor,
    )


#
# Base units [1, page 130, section 2.3.3] [2, page 20, table 4]
#
DIM_TIME = BaseDimension("T")
SECOND = BaseUnit("second", DIM_TIME)
"""Time (seconds)"""
DIM_LENGTH = BaseDimension("L")
METER = BaseUnit("meter", DIM_LENGTH)
"""Length (meters)"""
DIM_MASS = BaseDimension("M")
KILOGRAM = BaseUnit("kilogram", DIM_MASS)
"""Mass (kilograms)"""
DIM_ELECTRIC_CURRENT = BaseDimension("I")
AMPERE = BaseUnit("ampere", DIM_ELECTRIC_CURRENT)
"""Electric Current (amperes)"""
DIM_TEMPERATURE = BaseDimension("Θ")
KELVIN = BaseUnit("kelvin", DIM_TEMPERATURE)
"""Thermodynamic Temperature (kelvins)"""
DIM_AMOUNT = BaseDimension("N")
MOLE = BaseUnit("mole", DIM_AMOUNT)
"""Amount of Substance (moles)"""
DIM_J = BaseDimension("J")
CD = BaseUnit("candela", DIM_J)
"""Luminous Intensity (candelas)"""

#
# Derived Units [1, page 137, section 2.3.4] [2, page 22, table 5]
# important and widely used, but which do not properly fall within the SI.
#

RAD = Dimensionless("radian")
"""Plane angle (radians). Not to be confused with m m⁻¹."""
SR = Dimensionless("steradian")
"""Solid angle (steradians). Not to be confused with m² m⁻²."""
HZ = Mul((Exp(KILOGRAM, 1), Exp(METER, -1), Exp(SECOND, -1)), "hertz")
"""Frequency (hertz). Shall only be used for periodic phenomena."""
N = Mul((Exp(KILOGRAM, 1), Exp(METER, 1), Exp(SECOND, -2)), "newton")
"""Force (newtons)"""
PA = Mul((Exp(N, 1), Exp(METER, -2)), "pascal")
"""Pressure, stress (pascals)"""
J = Mul((Exp(N, 1), Exp(METER, 1)), "joule")
"""Energy, work, amount of heat (joules)"""
W = Mul((Exp(J, 1), Exp(SECOND, -1)), "watt")
"""Power, radiant flux (watts)"""
C = Mul((Exp(AMPERE, 1), Exp(SECOND, 1)), "coulomb")
"""Electric charge (coulombs)"""
V = Mul((Exp(W, 1), Exp(AMPERE, -1)), "volt")
"""Electric potential difference, voltage (volts).
Also named "electric tension" or "tension"."""
F = Mul((Exp(C, 1), Exp(V, -1)), "farad")
"""Capacitance (farads)"""
OHM = Mul((Exp(V, 1), Exp(AMPERE, -1)), "ohm")
"""Electric resistance (ohms)"""
SIEMENS = Mul((Exp(AMPERE, 1), Exp(V, -1)), "siemens")
"""Electric conductance (siemens)"""
WB = Mul((Exp(V, 1), Exp(SECOND, 1)), "weber")
"""Magnetic flux (webers)"""
T = Mul((Exp(WB, 1), Exp(METER, -2)), "tesla")
"""Magnetic flux density (teslas)"""
H = Mul((Exp(WB, 1), Exp(AMPERE, -1)), "henry")
"""Inductance (henries)"""
DEGC = Mul((Exp(KELVIN, 1),), "degree_celsius")
"""Celsius temperature (degrees Celsius).
The numerical value of a temperature difference is the same when expressed
in either degrees Celsius or in Kelvins."""
# NOTE: The symbol `sr` for must be included to distinguish luminous flux (lumen)
# from luminous intensity (candela)
LM = Mul((Exp(CD, 1), Exp(SR, 1)), "lumen")
"""Luminous flux (lumens)"""
LX = Mul((Exp(LM, 1), Exp(METER, -2)), "lux")
"""Illuminance (lux)"""
BQ = Mul((Exp(SECOND, -1),), "becquerel")
"""Activity referred to a radionuclide (becquerels). Shall only be used for
stochastic processes in activity referred to a radionuclide.
Not to be confused with "radioactivity"."""
GY = Mul((Exp(J, 1), Exp(KILOGRAM, -1)), "gray")
"""Absorbed dose, kerma (grays)"""
SV = Mul((Exp(J, 1), Exp(KILOGRAM, -1)), "sievert")
"""Dose equivalent (sieverts)"""
KAT = Mul((Exp(MOLE, 1), Exp(SECOND, -1)), "katal")
"""Catalytic activity (katal)"""

MIN = Scaled("minute", SECOND, factor=60)
HOUR = Scaled("hour", SECOND, factor=3600)
DAY = Scaled("day", HOUR, factor=24)
YEAR = Scaled("year", DAY, factor=365.25)  # on average

FEET = Scaled("feet", METER, factor=0.3048)
