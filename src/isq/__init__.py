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

[2] "NIST Handbook 44 - 2024 - Appendix C. General Tables of Units of
Measurement," NIST,
Available: https://www.nist.gov/document/nist-handbook-44-2024-appendix-c-pdf
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Generic, Literal, TypeVar, Union

from typing_extensions import TypeAlias

_ExpressionKind: TypeAlias = Literal["dimensionless", "unit", "dimension"]
_K = TypeVar("_K", bound=_ExpressionKind)


class Expr(Generic[_K]):
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
            return self.terms[0].base.kind
        else:
            raise TypeError(
                f"cannot determine kind for unknown expression type: {type(self)}"
            )


@dataclass(frozen=True)
class Dimensionless(Expr[Literal["dimensionless"]]):
    name: str
    """Name for the dimensionless number, e.g. `reynolds`, `stanton`"""


@dataclass(frozen=True)
class BaseDimension(Expr[Literal["dimension"]]):
    name: str
    """Name for the base dimension, e.g. `L`, `M`, `T`"""


@dataclass(frozen=True)
class BaseUnit(Expr[Literal["unit"]]):
    name: str
    """Name for the unit, e.g. `m`, `kg`, `s`"""
    dimension: BaseDimension
    """Reference to the base dimension"""


Exponent: TypeAlias = Union[int, Fraction]
"""An exponent, generally small integers, which can be positive, negative,
or a fraction, but not zero"""


@dataclass(frozen=True)
class Exp(Expr[_K]):
    """A base unit raised to an exponent.
    For example, `BaseUnit("meter", Dimension("L")), 2)` is m²."""

    base: Expr[_K]
    """Base unit, dimension or dimensionless number"""
    exponent: Exponent
    """Exponent. Avoid using zero to represent dimensionless numbers: 
    use [isq.Dimensionless][] with a name instead."""

    @property
    def _is_root_node(self) -> bool:
        return isinstance(self.base, (BaseUnit, BaseDimension, Dimensionless))

    def __post_init__(self) -> None:
        if self.exponent == 0:
            raise ValueError("exponent must not be zero, use `Dimensionless`")


@dataclass(frozen=True)
class Mul(Expr[_K]):
    """Recursively-defined products of powers of an expression."""

    terms: tuple[Exp[_K], ...]
    """A tuple of base units raised to an exponent, or any mix of expressions
    (including [isq.Mul][] itself)"""
    name: str | None = None
    """Name for this expression, e.g. `newton`, `joule`"""

    def __post_init__(self) -> None:
        n_terms = len(self.terms)
        if n_terms == 0:
            raise ValueError("terms must not be empty, use `Dimensionless`")
        unique_kinds = len(set(t.base.kind for t in self.terms))
        if unique_kinds != 1:
            raise ValueError("terms must all be either `unit` or `dimension`")

    def simplify(self) -> Mul[_K] | Dimensionless:
        """Return the canonical-form of the expression. Flattens the tree-like
        structure into products of powers of base units."""
        base_exponent_pairs: dict[Expr[_K], Exponent] = {}
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
    terms: tuple[Exp[_K], ...],
    base_exponent_pairs_mut: dict[Expr[_K], Exponent],
) -> None:
    for term in terms:
        if term._is_root_node:
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
        else:
            raise ValueError(f"unknown expression {term}")


# 2.3.3
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
DIM_CANDELA = BaseUnit("candela", DIM_J)
"""Luminous Intensity (candelas)"""
