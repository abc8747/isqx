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

    def simplify(self) -> Mul | Dimensionless:
        """Return the canonical-form of the expression. Flattens the tree-like
        structure into products of powers of base units."""
        base_exponent_pairs: dict[Expr, Exponent] = {}
        _insert_root_terms(self.terms, base_exponent_pairs)
        # NOTE: Exp(..., 0) is not allowed, create a new one for disambiguation
        if all(exponent == 0 for exponent in base_exponent_pairs.values()):
            new_name = f"simplified_{hash(self)}"
            return Dimensionless(new_name)
        base_exponent_pairs_sorted = sorted(
            base_exponent_pairs.items(),
            key=lambda item: item[0].name,  # type: ignore
        )
        return Mul(
            tuple(
                Exp(base, exponent)
                for base, exponent in base_exponent_pairs_sorted
            )
        )


def _insert_root_terms(
    terms: tuple[Exp, ...],
    base_exponent_pairs_mut: dict[Expr, Exponent],
) -> None:
    for term in terms:
        if isinstance(term.base, (BaseUnit, BaseDimension, Dimensionless)):
            base_exponent_pairs_mut.setdefault(term.base, 0)
            base_exponent_pairs_mut[term.base] += term.exponent
        elif isinstance(term.base, Mul):
            terms_distributed = tuple(
                Exp(term_inner.base, term_inner.exponent * term.exponent)
                for term_inner in term.base.terms
            )
            _insert_root_terms(terms_distributed, base_exponent_pairs_mut)
        elif isinstance(term.base, Exp):
            term_inner = term.base
            term_distributed = Exp(
                term_inner.base, term_inner.exponent * term.exponent
            )
            _insert_root_terms((term_distributed,), base_exponent_pairs_mut)
        elif isinstance(term.base, Derived):
            raise NotImplementedError
        else:
            raise ValueError(f"unknown expression {term}")


@dataclass(frozen=True)
class Derived(Expr):
    name: str
    """Name of the derived unit."""
    reference_expr: Expr
    """The unit or dimension that this derived unit is derived from."""
    to_reference: Callable[[Any], Any]
    """Converts a value from derived to reference unit."""
    to_derived: Callable[[Any], Any]
    """Converts a value from reference to derived unit."""


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


FOOT = Derived(
    "foot",
    METER,
    to_reference=lambda ft: ft * 0.3048,
    to_derived=lambda m: m / 0.3048,
)
