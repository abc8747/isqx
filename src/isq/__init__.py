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
from typing import Any, Literal, Protocol, Union, runtime_checkable

from typing_extensions import TypeAlias

_ExpressionKind: TypeAlias = Literal["dimensionless", "unit", "dimension"]


@runtime_checkable
class Expr(Protocol):
    """Trait representing a tree-like unit or dimension expression."""

    @property
    def dimension(self) -> Expr: ...

    @property
    def kind(self) -> _ExpressionKind: ...

    def simplify(self) -> Expr:
        """Flatten the tree-like structure into a canonical form.

        Examples:

        - `Exp(Exp(M, 2), 3)` → `Exp(M, 6)`
        - `Mul((Exp(M, 2), Exp(M, -2)))` → `Dimensionless`
        - `Exp(Mul((Exp(M, 1), Exp(S, -1))), 2)` →
          `Mul((Exp(M, 2), Exp(S, -2)))`
        - `Scaled(Scaled(M, 2), 3)` → `Scaled(M, 6)`
        - `Scaled(Mul((Exp(Scaled(M, 2), 3), Exp(Scaled(S, 3), 2))), 6)` →
          `Scaled(Mul((Exp(M, 3), Exp(S, 2)), 72))`
        - `Mul((Exp(HOUR, 1), Exp(DAY, -1)))` →
          `Scaled(Dimensionless, 1 / 24)`
        """
        # TODO: add new parameter `keep_scaled: bool = False`
        # if `keep_scaled`, ft² will not be simplified to m²
        ...  # pragma: no cover

    def to(self, target: Expr) -> _Converter:
        """Return a converter object, that when called with a value, converts it
        to the target unit or dimension.

        :param target: The target unit or dimension to convert to. Must have
            compatible dimensions with the origin.
        """
        # NOTE: not using mixins because we want to track coverage
        # TODO: add new parameter `exact: bool = False` for money conversions
        ...  # pragma: no cover


@dataclass(frozen=True)
class Dimensionless(Expr):
    name: str
    """Name for the dimensionless number, e.g. `reynolds`, `stanton`"""

    @property
    def dimension(self) -> Dimensionless:
        return self

    @property
    def kind(self) -> _ExpressionKind:
        return "dimensionless"

    def simplify(self) -> Expr:
        return self

    def to(self, target: Expr) -> _Converter:
        return _Converter.new(origin=self, target=target)


@dataclass(frozen=True)
class BaseDimension(Expr):
    name: str
    """Name for the base dimension, e.g. `L`, `M`, `T`"""

    @property
    def dimension(self) -> BaseDimension:
        return self

    @property
    def kind(self) -> _ExpressionKind:
        return "dimension"

    def simplify(self) -> Expr:
        return self

    def to(self, target: Expr) -> _Converter:
        return _Converter.new(origin=self, target=target)


@dataclass(frozen=True)
class BaseUnit(Expr):
    _dimension: BaseDimension
    """Reference to the base dimension"""
    name: str
    """Name for the unit, e.g. `m`, `kg`, `s`"""

    @property
    def dimension(self) -> BaseDimension:
        return self._dimension

    @property
    def kind(self) -> _ExpressionKind:
        return "unit"

    def simplify(self) -> Expr:
        return self

    def to(self, target: Expr) -> _Converter:
        return _Converter.new(origin=self, target=target)


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
    """Base unit, dimension, dimensionless number or [isq.Exp][] itself."""
    exponent: Exponent
    """Exponent. Avoid using zero to represent dimensionless numbers: 
    use [isq.Dimensionless][] with a name instead."""

    def __post_init__(self) -> None:
        if self.exponent == 0:
            raise ValueError("exponent must not be zero, use `Dimensionless`")

    @property
    def kind(self) -> _ExpressionKind:
        return self.base.kind

    @property
    def dimension(self) -> Exp:
        return Exp(self.base.dimension, self.exponent)

    def simplify(self) -> Expr:
        base_exponent_pairs: dict[Expr, Exponent] = {}
        derived_conversions: list[tuple[Scaled, Exponent]] = []
        _insert_root_expr(self, base_exponent_pairs, derived_conversions)
        return _get_simplified_expression(
            base_exponent_pairs,
            derived_conversions,
            output_name_maybe=f"expr_{hash(self)}",
        )

    def to(self, target: Expr) -> _Converter:
        return _Converter.new(origin=self, target=target)


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

    @property
    def dimension(self) -> Mul:
        return Mul(
            tuple(term.dimension for term in self.terms),
            name=self.name,
        )

    @property
    def kind(self) -> _ExpressionKind:
        # all terms have a consistent underlying kind (unit/dimension)
        for term in self.terms:
            term_kind = term.base.kind
            if term_kind != "dimensionless":
                return term_kind
        # everything left are dimensionless to the power of something
        return "dimensionless"

    def simplify(self) -> Expr:
        base_exponent_pairs: dict[Expr, Exponent] = {}
        derived_conversions: list[tuple[Scaled, Exponent]] = []
        for term in self.terms:
            _insert_root_expr(term, base_exponent_pairs, derived_conversions)
        return _get_simplified_expression(
            base_exponent_pairs,
            derived_conversions,
            output_name_maybe=self.name or f"expr_{hash(self)}",
        )

    def to(self, target: Expr) -> _Converter:
        return _Converter.new(origin=self, target=target)


@dataclass(frozen=True)
class Scaled(Expr):
    reference: Expr
    """The unit or dimension that this unit or dimension is based on."""
    factor: float | Fraction
    """Multiplying this factor converts this value into the reference.
    For example, `1 ft = 0.3048 m`, so the factor is 0.3048.
    
    !!! note
        If the factor is a `Fraction`, the `to` method may compute conversions
        exactly. However, using `numpy` arrays with `Fraction` will return dtype
        `object`, which hurts performance. Furthermore, since `jax` and `torch`
        do not support multiplication with `Fraction`, it is highly recommended
        to use `float` for the factor.
    """
    name: str
    """Name of this unit or dimension."""
    # TODO: remove add "exact factor" that is a `Decimal` or `Fraction`

    def to_reference(self, value: Any) -> Any:
        """Convert a value in this unit to the reference unit."""
        return value * self.factor

    def from_reference(self, value: Any) -> Any:
        """Convert a value in the reference unit to this unit."""
        return value / self.factor

    @property
    def kind(self) -> _ExpressionKind:
        return self.reference.kind

    @property
    def dimension(self) -> Expr:
        return self.reference.dimension

    def simplify(self) -> Scaled:
        expr, factor = _flatten_scaled_nested(self.reference, self.factor)
        return Scaled(expr, factor, name=self.name)

    def to(self, target: Expr) -> _Converter:
        return _Converter.new(origin=self, target=target)


#
# simplification
#


def _flatten_scaled_nested(
    expr: Scaled | Expr,
    factor: float | Fraction,
) -> tuple[Expr, float | Fraction]:
    if not isinstance(expr, Scaled):
        return expr.simplify(), factor
    return _flatten_scaled_nested(expr.reference, factor * expr.factor)


def _insert_root_expr(
    exp: Exp,
    base_exponent_pairs_mut: dict[Expr, Exponent],
    scaled_conversions_mut: list[tuple[Scaled, Exponent]],
) -> None:
    if isinstance(exp.base, (Dimensionless, BaseDimension, BaseUnit)):
        base_exponent_pairs_mut.setdefault(exp.base, 0)
        base_exponent_pairs_mut[exp.base] += exp.exponent
    elif isinstance(exp.base, Exp):
        exp_inner = exp.base
        _insert_root_expr(
            Exp(exp_inner.base, exp_inner.exponent * exp.exponent),
            base_exponent_pairs_mut,
            scaled_conversions_mut,
        )
    elif isinstance(exp.base, Mul):
        for exp_inner in exp.base.terms:
            _insert_root_expr(
                Exp(exp_inner.base, exp_inner.exponent * exp.exponent),
                base_exponent_pairs_mut,
                scaled_conversions_mut,
            )
    elif isinstance(exp.base, Scaled):
        expr_derived = exp.base
        scaled_conversions_mut.append((expr_derived, exp.exponent))
        _insert_root_expr(
            Exp(expr_derived.reference, exp.exponent),
            base_exponent_pairs_mut,
            scaled_conversions_mut,
        )
    else:  # pragma: no cover
        raise ValueError(f"unknown expression {exp}")


def _get_simplified_expression(
    base_exponent_pairs: dict[Expr, Exponent],
    scaled_conversions: list[tuple[Scaled, Exponent]],
    *,
    output_name_maybe: str,
) -> Expr:
    no_conversions_involved = not scaled_conversions
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

    # NOTE: if `Scaled.factor` is a `Fraction`, the returned `Scaled.factor`
    # will be a `float` and precison issues.
    # TODO: return exact representation only if `use_exact = True` in the future
    factor_final: float = 1.0
    for scaled, exponent in scaled_conversions:
        factor_final *= scaled.factor**exponent

    return Scaled(
        reference=simplified_expr,
        factor=factor_final,
        name=output_name_maybe,
    )


#
# unit/dimension conversions
#


@dataclass(frozen=True)
class _Converter:
    origin_simpl: Expr
    target_simpl: Expr
    factor: float | Fraction

    @classmethod
    def new(cls, origin: Expr, target: Expr) -> _Converter:
        """Create a new unit converter from one unit to another."""
        origin_simpl = origin.simplify()
        target_simpl = target.simplify()
        if origin_simpl.kind != target_simpl.kind:
            raise ValueError(
                "expected self and target to have the same kind, "
                f"but {origin_simpl.kind} != {target_simpl.kind}"
            )

        origin_inner_simpl, origin_factor = _get_factor(origin_simpl)
        target_inner_simpl, target_factor = _get_factor(target_simpl)
        dim_origin_simpl: Any = origin_inner_simpl.dimension
        dim_target_simpl: Any = target_inner_simpl.dimension
        # ensure `Mul` equality checks for terms, not including the name attr
        if isinstance(dim_origin_simpl, Mul):
            dim_origin_simpl = dim_origin_simpl.terms
        if isinstance(dim_target_simpl, Mul):
            dim_target_simpl = dim_target_simpl.terms
        if dim_origin_simpl != dim_target_simpl:
            raise ValueError(
                f"expected origin and target to have the same dimension, "
                f"but {dim_origin_simpl} != {dim_target_simpl}"
            )
        return cls(
            origin_simpl=origin_simpl,
            target_simpl=target_simpl,
            factor=origin_factor / target_factor,
        )

    def __call__(self, value: Any) -> Any:
        """Convert a value in the origin unit to the target unit."""
        return value * self.factor


def _get_factor(expr_simpl: Expr) -> tuple[Expr, float | Fraction]:
    """Get the inner expression and the factor of a simplified expression."""

    if isinstance(expr_simpl, (BaseUnit, BaseDimension, Dimensionless)):
        return expr_simpl, 1.0
    elif isinstance(expr_simpl, Exp):
        # if expr is `Exp(Scaled(x, a), b)`, simplifying will result in
        # `Scaled(Exp(x, b), a * b)` so it'll be handled by the `Scaled` case
        return expr_simpl, 1.0
    elif isinstance(expr_simpl, Mul):
        # similarly, `Mul((Scaled(...),))` → `Scaled(Mul((...),),)`
        return expr_simpl, 1.0
    elif isinstance(expr_simpl, Scaled):
        # so `Scaled` should always be pushed to outmost level.
        # furthermore, since nested `Scaled(Scaled(x, c), d)` would simplify to
        # `Scaled(x, c * d)`, we don't need to recursively get the factor.
        return expr_simpl.reference, expr_simpl.factor
    else:  # pragma: no cover
        raise ValueError(f"unknown expression {expr_simpl}")


#
# base units [1, page 130, section 2.3.3] [2, page 20, table 4]
#

DIM_TIME = BaseDimension("T")
S = BaseUnit(DIM_TIME, "second")
"""Time (seconds)"""
DIM_LENGTH = BaseDimension("L")
M = BaseUnit(DIM_LENGTH, "meter")
"""Length (meters)"""
DIM_MASS = BaseDimension("M")
KG = BaseUnit(DIM_MASS, "kilogram")
"""Mass (kilograms)"""
DIM_CURRENT = BaseDimension("I")
A = BaseUnit(DIM_CURRENT, "ampere")
"""Electric Current (amperes)"""
DIM_TEMPERATURE = BaseDimension("Θ")
K = BaseUnit(DIM_TEMPERATURE, "kelvin")
"""Thermodynamic Temperature (kelvins)"""
DIM_AMOUNT = BaseDimension("N")
MOLE = BaseUnit(DIM_AMOUNT, "mole")
"""Amount of Substance (moles)"""
DIM_LUMINOUS_INTENSITY = BaseDimension("J")
CD = BaseUnit(DIM_LUMINOUS_INTENSITY, "candela")
"""Luminous Intensity (candelas)"""

#
# derived Units [1, page 137, section 2.3.4] [2, page 22, table 5]
# important and widely used, but which do not properly fall within the SI.
#

RAD = Dimensionless("radian")
"""Plane angle (radians). Not to be confused with m m⁻¹."""
SR = Dimensionless("steradian")
"""Solid angle (steradians). Not to be confused with m² m⁻²."""
HZ = Mul((Exp(KG, 1), Exp(M, -1), Exp(S, -1)), "hertz")
"""Frequency (hertz). Shall only be used for periodic phenomena."""
N = Mul((Exp(KG, 1), Exp(M, 1), Exp(S, -2)), "newton")
"""Force (newtons)"""
PA = Mul((Exp(N, 1), Exp(M, -2)), "pascal")
"""Pressure, stress (pascals)"""
J = Mul((Exp(N, 1), Exp(M, 1)), "joule")
"""Energy, work, amount of heat (joules)"""
W = Mul((Exp(J, 1), Exp(S, -1)), "watt")
"""Power, radiant flux (watts)"""
C = Mul((Exp(A, 1), Exp(S, 1)), "coulomb")
"""Electric charge (coulombs)"""
V = Mul((Exp(W, 1), Exp(A, -1)), "volt")
"""Electric potential difference, voltage (volts).
Also named "electric tension" or "tension"."""
F = Mul((Exp(C, 1), Exp(V, -1)), "farad")
"""Capacitance (farads)"""
OHM = Mul((Exp(V, 1), Exp(A, -1)), "ohm")
"""Electric resistance (ohms)"""
SIEMENS = Mul((Exp(A, 1), Exp(V, -1)), "siemens")
"""Electric conductance (siemens)"""
WB = Mul((Exp(V, 1), Exp(S, 1)), "weber")
"""Magnetic flux (webers)"""
T = Mul((Exp(WB, 1), Exp(M, -2)), "tesla")
"""Magnetic flux density (teslas)"""
H = Mul((Exp(WB, 1), Exp(A, -1)), "henry")
"""Inductance (henries)"""
# NOTE: degree celsius is a special case: ℃² does not equal K² so we don't
# define it as a scaled unit of kelvin.
DEGC = BaseUnit(DIM_TEMPERATURE, "degree_celsius")
"""Celsius temperature (degrees Celsius).
The numerical value of a temperature difference is the same when expressed
in either degrees Celsius or in Kelvins."""
# NOTE: The symbol `sr` for must be included to distinguish luminous flux (lumen)
# from luminous intensity (candela)
LM = Mul((Exp(CD, 1), Exp(SR, 1)), "lumen")
"""Luminous flux (lumens)"""
LX = Mul((Exp(LM, 1), Exp(M, -2)), "lux")
"""Illuminance (lux)"""
BQ = Mul((Exp(S, -1),), "becquerel")
"""Activity referred to a radionuclide (becquerels). Shall only be used for
stochastic processes in activity referred to a radionuclide.
Not to be confused with "radioactivity"."""
GY = Mul((Exp(J, 1), Exp(KG, -1)), "gray")
"""Absorbed dose, kerma (grays)"""
SV = Mul((Exp(J, 1), Exp(KG, -1)), "sievert")
"""Dose equivalent (sieverts)"""
KAT = Mul((Exp(MOLE, 1), Exp(S, -1)), "katal")
"""Catalytic activity (katal)"""

MIN = Scaled(S, 60, "minute")
HOUR = Scaled(MIN, 60, "hour")
DAY = Scaled(HOUR, 24, "day")
YR = Scaled(DAY, 365.25, "year")  # on average
DECADE = Scaled(YR, 10, "decade")
CENTURY = Scaled(DECADE, 10, "century")

FT = Scaled(M, 0.3048, "feet")


@dataclass(frozen=True)
class Disambiguation:
    dimension: Expr  # e.g. meter

    def __call__(self, unit: Expr) -> Expr:
        # TODO: check dimension compatibility
        raise NotImplementedError


GEOPOTENTIAL_ALTITUDE = Disambiguation(DIM_LENGTH)
