from __future__ import annotations

import decimal
import math
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import (
    Any,
    Final,
    Generator,
    Hashable,
    Literal,
    Mapping,
    MutableMapping,
    MutableSequence,
    NamedTuple,
    Protocol,
    Sequence,
    SupportsFloat,
    Union,
    final,
    overload,
    runtime_checkable,
)

from typing_extensions import TypeAlias


@runtime_checkable
class SupportsDecimal(SupportsFloat, Protocol):
    def to_decimal(self, ctx: decimal.Context) -> Decimal: ...


ExpressionKind: TypeAlias = Literal["dimensionless", "unit", "dimension"]
Factor: TypeAlias = Union[SupportsDecimal, Decimal, Fraction, float, int]


@runtime_checkable
class Expr(Protocol):
    """A protocol that a "unit-like" expression must implement.

    It may be of the following forms:

    | Type                                       | Example                   |
    | ------------------------------------------ | ------------------------- |
    | [dimensionless number][isq.Dimensionless]¹ | `Reynolds`, `Prandtl`     |
    | [base dimension][isq.BaseDimension]¹       | [length][isq.DIM_LENGTH]  |
    | [base unit][isq.BaseUnit]¹                 | [meter][isq.M]            |
    | [expression raised to a power][isq.Exp]²   | `Exp(M, 2)`               |
    | [product of expressions][isq.Mul]²         | `Mul(A, S)`               |
    | [scaled expression][isq.Scaled]²⁴          | `Scaled(M, 0.3048)`       |
    | [aliased][isq.Aliased]¹                    | [newton][isq.N] = kg m s⁻²|
    | [translated expression][isq.Translated]³   | `Translated(K, -273.15)`  |
    | [logarithmic quantity][isq.Logarithmic]¹³  | [decibel-volt][isq.DBV]   |
    | [tagged][isq.Tagged]⁵                      | true vs ground speed      |

    ¹ these expressions are associated with a [name][isq.NamedExpr].
    ² these expressions can be [aliased with a name][isq.Aliased].
    ³ these expressions are *terminal*, meaning it cannot be further
      [exponentiated][isq.Exp], [multiplied][isq.Mul], [scaled][isq.Scaled],
      [translated][isq.Translated] or [aliased][isq.Aliased] to form a more
      complex expression. However, it can be further [tagged][isq.Tagged]
      (e.g. surface temperature vs ISA temperature).
    ⁴ can be created by multiplying a [prefix][isq.Prefix] (e.g. `milli`)
    ⁵ can be created by indexing a [quantity kind][isq.QtyKind] with a unit
    """

    @property
    def dimension(self) -> Expr:
        """Return the dimension of this "unit-like" expression.
        Note that it does not perform simplification.

        Examples:

        - `Exp(M, 2)` -> `Exp(DIM_LENGTH, 2)`
        - `Mul(M, Exp(S, -1))` -> `Mul(DIM_LENGTH, Exp(DIM_TIME, -1))`
        """
        ...

    @property
    def kind(self) -> ExpressionKind:
        """Whether this expression is a unit, dimension, or dimensionless."""
        ...

    def simplify(self) -> Expr:
        """Flatten a complex tree-like structure into a simple canonical form,
        including: distributing exponents, combining like terms and merging
        nested scaling factors. This strips away [aliases][isq.Aliased] but
        keeps [tags][isq.Tagged] intact.

        Examples:

        - `Exp(Exp(M, 2), 3)` → `Exp(M, 6)`
        - `Mul((Exp(M, 2), Exp(M, -2)))` → `Dimensionless`
        - `Exp(Mul((M, Exp(S, -1))), 2)` → `Mul((Exp(M, 2), Exp(S, -2)))`
        - `Scaled(Scaled(M, 2), 3)` → `Scaled(M, LazyFactor((3, 2)))`
        - `Scaled(Mul((Exp(Scaled(M, 2), 3), Exp(Scaled(S, 3), 2))), 6)` →
          `Scaled(Mul((Exp(M, 3), Exp(S, 2)), 432))`
        - `Mul((HOUR, Exp(DAY, -1)))` →
          `Scaled(Dimensionless, 1 / 24)`
        """
        ...

    # TODO: in the future, we want a as_basis() function that accepts set[Expr]
    # why: we sometimes want to re-express some unit not in MKS, but CGS
    # that will require linear algebra to solve the dimensional exponents but
    # we're leaving that as optional and far in the future.


@runtime_checkable
class NamedExpr(Expr, Protocol):
    name: str
    """A name for this expression, e.g. `meter`, `newton`, `reynolds`"""


class AliasMixin:
    def alias(self, name: str, *, allow_prefix: bool = False) -> Aliased:
        """Wrap this expression with a name.

        :param name: Name of this alias, e.g. `newton`
        :param allow_prefix: Whether to allow [prefixes][isq.Prefix] to be
        attached. This should only be true for some units like `liter`
        """
        return Aliased(self, name=name, allow_prefix=allow_prefix)  # type: ignore


class TagMixin:
    def tag(self, context: Hashable) -> Tagged:
        """Wrap this expression with some context.

        :param context: A hashable identifier, e.g. `geopotential`, or
        a tuple of contexts
        """
        return Tagged(self, context=context)  # type: ignore


class ConvertMixin:
    def to(
        self: Expr,
        target: Expr,
        *,
        exact: bool = False,
        ctx: decimal.Context | None = None,
    ) -> Converter:
        """Return a converter object, that when called with a value, converts it
        to the target unit or dimension.

        :param target: The target unit or dimension to convert to. Must have
            compatible dimensions with the origin.
        """
        ctx = ctx or decimal.getcontext()
        return Converter.new(origin=self, target=target, exact=exact, ctx=ctx)


class OpsMixin:
    """Operator overloads to allow ergonomic expression construction.

    !!! note
        While dividing expressions is supported, it is strongly discouraged as
        it can lead to operator precedence ambiguity. For instance, while Python
        interprets `J / KG / K` as `(J / KG) / K`, it is often clearer to
        represent it as `J * KG**-1 * K**-1`.
    """

    def __pow__(self: Expr, exponent: Exponent) -> Exp:
        return Exp(self, exponent)

    @overload
    def __mul__(self: Expr, rhs: Expr) -> Mul: ...

    @overload
    def __mul__(self: Expr, rhs: LazyFactor | Factor) -> Scaled: ...

    def __mul__(self: Expr, rhs: Expr | LazyFactor | Factor) -> Mul | Scaled:
        if isinstance(
            rhs, (LazyFactor, SupportsDecimal, Decimal, Fraction, float, int)
        ):
            return Scaled(self, rhs)
        # make sure KG * M * S becomes flat, not Mul((Mul((KG, M)), S))
        terms_self = self.terms if isinstance(self, Mul) else (self,)
        terms_other = rhs.terms if isinstance(rhs, Mul) else (rhs,)
        return Mul(tuple([*terms_self, *terms_other]))

    def __rmul__(self: Expr, lhs: LazyFactor | Factor) -> Scaled:
        return Scaled(self, lhs)

    @overload
    def __truediv__(self: Expr, rhs: Expr) -> Mul: ...

    @overload
    def __truediv__(self: Expr, rhs: LazyFactor | Factor) -> Scaled: ...

    def __truediv__(
        self: Expr, rhs: Expr | LazyFactor | Factor
    ) -> Mul | Scaled:
        if not isinstance(rhs, Expr):  # M / 2 => Scaled(M, Fraction(1, 2))
            return Scaled(
                self, LazyFactor(tuple(f for f in _products_inverse(rhs)))
            )
        return self * rhs**-1  # type: ignore


@dataclass(frozen=True)
class Dimensionless(OpsMixin, ConvertMixin, TagMixin, NamedExpr):
    name: str
    """Name for the dimensionless number, e.g. `reynolds`, `prandtl`"""

    @property
    def dimension(self) -> Dimensionless:
        return self

    @property
    def kind(self) -> ExpressionKind:
        return "dimensionless"

    def simplify(self) -> Dimensionless:
        return self


@dataclass(frozen=True)
class BaseDimension(OpsMixin, ConvertMixin, TagMixin, NamedExpr):
    name: str
    """Name for the base dimension, e.g. `L`, `M`, `T`"""

    @property
    def dimension(self) -> BaseDimension:
        return self

    @property
    def kind(self) -> ExpressionKind:
        return "dimension"

    def simplify(self) -> BaseDimension:
        return self


@dataclass(frozen=True)
class BaseUnit(OpsMixin, ConvertMixin, TagMixin, NamedExpr):
    _dimension: BaseDimension
    """Reference to the base dimension"""
    name: str
    """Name for the unit, e.g. `m`, `kg`, `s`"""

    @property
    def dimension(self) -> BaseDimension:
        return self._dimension

    @property
    def kind(self) -> ExpressionKind:
        return "unit"

    def simplify(self) -> BaseUnit:
        return self


Exponent: TypeAlias = Union[int, Fraction]
"""An exponent, generally small integers, which can be positive, negative,
or a fraction, but not zero"""


@dataclass(frozen=True)
class Exp(OpsMixin, ConvertMixin, TagMixin, AliasMixin, Expr):
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
        if not isinstance(self.exponent, (int, Fraction)):
            raise CompositionError(
                msg=(
                    "exponent must be an integer or a fraction, "
                    f"not {self.exponent} ({type(self.exponent).__name__})"
                )
            )
        if self.exponent == 0:
            raise CompositionError(
                msg="exponent must not be zero.",
                help="use `Dimensionless`.",
            )
        ref = _unwrap_tagged_or_aliased(self.base)
        if isinstance(ref, Translated):
            raise TerminalUnitError(
                expr=ref,
                op=Exp,
                help=(
                    "did you mean to exponentiate its "
                    f"absolute reference `{ref.reference}` instead?"
                ),
            )  # prevent ℃². J ℃⁻¹ should be written as J K⁻¹
        if isinstance(ref, Logarithmic):
            raise TerminalUnitError(
                expr=ref,
                op=Exp,
                note="logarithmic units cannot be raised to a power.",
            )

    @property
    def dimension(self) -> Exp:
        return Exp(self.base.dimension, self.exponent)

    @property
    def kind(self) -> ExpressionKind:
        return self.base.kind

    def simplify(self) -> Expr:
        """Flattens the expression by distributing exponents inward.

        This is the first step of simplification, ensuring expressions like
        (m/s)² correctly become m² / s² before terms are combined.
        """
        base_exponent_pairs: dict[Expr, Exponent] = {}
        derived_conversions: list[tuple[Scaled, Exponent]] = []
        _decompose_expr(
            self.base, self.exponent, base_exponent_pairs, derived_conversions
        )
        return _build_canonical_expr(base_exponent_pairs, derived_conversions)


@dataclass(frozen=True)
class Mul(OpsMixin, ConvertMixin, TagMixin, AliasMixin, Expr):
    """Products of powers of an expression."""

    terms: tuple[Expr, ...]
    """A tuple of expressions to be multiplied, preserving the order."""

    def __post_init__(self) -> None:
        if not self.terms:
            raise CompositionError(
                msg="`Mul` terms must not be empty.",
                help="use `Dimensionless`.",
            )
        kinds = []
        for term in self.terms:
            ref = _unwrap_tagged_or_aliased(term)
            if isinstance(ref, Translated):
                raise TerminalUnitError(
                    expr=ref,
                    op=Mul,
                    help=(
                        f"use its absolute reference `{ref.reference}` "
                        f"in the product instead."
                    ),
                )  # prevent ℃ * ℃
            if isinstance(ref, Logarithmic):
                raise TerminalUnitError(
                    expr=ref,
                    op=Mul,
                    note="logarithmic units cannot be part of a product.",
                )
            kinds.append(term.kind)
        unique_kinds = set(kinds) - {"dimensionless"}
        if len(unique_kinds) != 1:
            raise MixedKindError(terms=self.terms)

    @property
    def dimension(self) -> Mul:
        return Mul(tuple(term.dimension for term in self.terms))

    @property
    def kind(self) -> ExpressionKind:
        # all terms have a consistent underlying kind (unit/dimension)
        for term in self.terms:
            term_kind = term.kind
            if term_kind != "dimensionless":
                return term_kind
        # everything left are dimensionless to the power of something
        return "dimensionless"

    def simplify(self) -> Expr:
        """Reduces the expression to its canonical product-of-powers form.

        This combines all like terms, so N * kg⁻¹ simplifies into m * s⁻².
        """
        base_exponent_pairs: dict[Expr, Exponent] = {}
        derived_conversions: list[tuple[Scaled, Exponent]] = []
        _decompose_expr(self, 1, base_exponent_pairs, derived_conversions)
        return _build_canonical_expr(base_exponent_pairs, derived_conversions)


@dataclass(frozen=True)
class Scaled(OpsMixin, ConvertMixin, TagMixin, AliasMixin, Expr):
    reference: Expr
    """The unit or dimension that this unit or dimension is based on."""
    factor: Factor | LazyFactor
    """The exact factor to multiply to this unit to convert it to the reference.
    For example, `1 ft = 0.3048 m`, so the factor is 0.3048.
    """

    def __post_init__(self) -> None:
        if not isinstance(
            self.factor,
            (LazyFactor, SupportsDecimal, Decimal, Fraction, float, int),
        ):
            raise CompositionError(
                msg=(
                    f"factor must be a number, "
                    f"not {self.factor} ({type(self.factor).__name__})"
                )
            )
        ref = _unwrap_tagged_or_aliased(self.reference)
        if isinstance(ref, Translated) or (
            isinstance(ref, Logarithmic) and not ref.allow_prefix
        ):
            raise TerminalUnitError(
                expr=self.reference,
                op=Scaled,
                note=(
                    "translated units (like ℃) and most"
                    "logarithmic units (like dBV) cannot be scaled."
                ),
            )  # prevent 13 * ℃, milli(decibel)

    @property
    def dimension(self) -> Expr:
        return self.reference.dimension

    @property
    def kind(self) -> ExpressionKind:
        return self.reference.kind

    def simplify(self) -> Expr:
        """Merges nested scaling factors into a single canonical expression."""
        base_exponent_pairs: dict[Expr, Exponent] = {}
        derived_conversions: list[tuple[Scaled, Exponent]] = []
        _decompose_expr(self, 1, base_exponent_pairs, derived_conversions)
        return _build_canonical_expr(base_exponent_pairs, derived_conversions)


@dataclass(frozen=True)
class Prefix:
    """A factory, which when multiplied by a [base unit][isq.BaseUnit] or
    [aliased unit][isq.Aliased], returns a [scaled unit][isq.Scaled].

    Note that this is not an [isq.Expr][], but a *constructor helper*.
    """

    factor: Factor
    name: str
    """Name of this prefix, e.g. `milli`, `kibi`"""

    def __mul__(self, rhs: BaseUnit | Aliased | Logarithmic) -> Aliased:
        if not isinstance(rhs, (BaseUnit, Aliased, Logarithmic)):
            raise PrefixError(
                prefix=self,
                target=rhs,
                note=(
                    "prefixes can only be applied to a `BaseUnit` or an `Alias`"
                    f", not `{type(rhs).__name__}`."
                ),
            )

        if isinstance(rhs, BaseUnit):
            if rhs.name == "kilogram":
                raise PrefixError(
                    prefix=self,
                    target=rhs,
                    note="cannot prefix KG, apply it to `GRAM` instead.",
                )
        elif isinstance(rhs, Aliased):
            if not rhs.allow_prefix:
                raise PrefixError(
                    prefix=self,
                    target=rhs,
                    note=f"aliased unit `{rhs.name}` does not allow prefixes.",
                )
            if self.name == "kilo" and rhs.name == "gram":
                raise PrefixError(
                    prefix=self,
                    target=rhs,
                    note="cannot apply `kilo` to `gram`. use `KG` directly.",
                )
        elif isinstance(rhs, Logarithmic):
            if not rhs.allow_prefix:
                raise PrefixError(
                    prefix=self,
                    target=rhs,
                    note=f"log unit `{rhs.name}` does not allow prefixes.",
                )

        new_name = f"{self.name}{rhs.name}"
        return Aliased(
            Scaled(rhs, self.factor), name=new_name, allow_prefix=False
        )

    # NOTE: not defining __rmul__ to avoid confusion


@dataclass(frozen=True)
class Aliased(OpsMixin, ConvertMixin, TagMixin, NamedExpr):
    """An alias for an expression, used to give a more readable name.

    Note that unlike a [tagged][isq.Tagged] expression,
    [simplification][isq.Expr.simplify] will effectively elide this class.
    """

    reference: Exp | Mul | Scaled
    """Expression to be aliased, e.g. `Mul((KG, M, Exp(S, -2)))`"""
    name: str
    """Name of this alias, e.g. `newton`"""
    allow_prefix: bool = False
    """Whether to allow [prefixes][isq.Prefix] to be attached.
    This should only be true for some units like `liter`."""

    def __post_init__(self) -> None:
        ref = self.reference
        if not isinstance(self.reference, (Exp, Mul, Scaled)):
            raise ReferenceTypeError(
                expr_type=Aliased,
                ref=ref,
                allowed_types_msg=("an `Exp`, `Mul`, or `Scaled` expression."),
            )

    @property
    def dimension(self) -> Expr:
        return self.reference.dimension

    @property
    def kind(self) -> ExpressionKind:
        return self.reference.kind

    def simplify(self) -> Expr:
        return self.reference.simplify()


@dataclass(frozen=True)
class Translated(OpsMixin, ConvertMixin, TagMixin, NamedExpr):
    """An expression offsetted from some reference unit."""

    reference: Expr
    """The expression that this expression is based on (e.g., `K` for `DEGC`)"""
    offset: Factor
    """The exact offset to add to the reference to get this unit.
    For example, `℃ = K - 273.15`, so the offset is -273.15."""
    name: str

    def __post_init__(self) -> None:
        ref = _unwrap_tagged_or_aliased(self.reference)
        if isinstance(ref, Translated):
            raise NestingError(expr_type=Translated)
        if not isinstance(ref, (BaseUnit, Scaled)):
            raise ReferenceTypeError(
                expr_type=Translated,
                ref=ref,
                allowed_types_msg="a `BaseUnit` or `Scaled` expression.",
            )

    @property
    def kind(self) -> ExpressionKind:
        return self.reference.kind

    @property
    def dimension(self) -> Expr:
        return self.reference.dimension

    def simplify(self) -> Translated:
        return Translated(self.reference.simplify(), self.offset, self.name)


@dataclass(frozen=True)
class Logarithmic(OpsMixin, ConvertMixin, TagMixin, NamedExpr):
    r"""A logarithmic unit, representing a level of a quantity.

    A level $L$ is defined as the ratio between a quantity to its reference:
    $$
    L = k \cdot \log_{b}\left(\frac{Q}{Q_\text{ref}}\right)
    $$
    The parameters $k$ and $b$ are determined by the specific unit:

    - Neper (Np): The coherent SI unit for level.
        - $b = e$
        - $k=1$ for field quantities (e.g., [V][isq.V], [A][isq.A], [Pa][isq.PA]).
        - $k=1/2$ for power quantities (e.g., [W][isq.W], W/m²).
    - Bel (B) and Decibel (dB):
        - $b = 10$
        - $k=20$ for field quantities.
        - $k=10$ for power quantities.
    """

    reference: BaseUnit | Exp | Mul | Scaled | Aliased
    """The linear unit being measured (e.g., V for dBV, W for dBm)"""
    quantity_type: Literal["power", "field"]
    """Whether the reference is a power or a field quantity."""
    log_base: Factor
    """The base of the logarithm (e.g., 10, 2, [isq.E][])"""
    name: str
    allow_prefix: bool = False
    """Whether prefixes can be applied to the logarithmic unit (e.g., mNp)."""

    def __post_init__(self) -> None:
        ref = _unwrap_tagged_or_aliased(self.reference)
        if isinstance(ref, (Logarithmic, Translated)):
            raise ReferenceTypeError(
                expr_type=Logarithmic,
                ref=ref,
                allowed_types_msg="a linear unit (e.g. `V`, `W`).",
                note=f"reference cannot be a `{type(ref).__name__}`.",
            )
        if ref.kind != "unit":
            raise ReferenceTypeError(
                expr_type=Logarithmic,
                ref=ref,
                allowed_types_msg="a reference with a physical unit.",
                note=f"the reference's kind is `{ref.kind}`, not `unit`.",
            )

    @property
    def level_factor(self) -> Factor:
        """Determines the multiplicative factor (e.g., 10 or 20 for dB)."""
        if self.log_base == 10:  # decibels
            return 10 if self.quantity_type == "power" else 20
        elif self.log_base is E:  # nepers
            return 1 if self.quantity_type == "field" else Fraction(1, 2)
        else:  # bits (log_base=2)
            return 1

    @property
    def dimension(self) -> Dimensionless:
        return Dimensionless(f"log_level_{hash(self)}")

    @property
    def kind(self) -> Literal["dimensionless"]:
        return "dimensionless"

    def simplify(self) -> Logarithmic:
        return Logarithmic(
            self.reference.simplify(),  # type: ignore
            self.quantity_type,
            self.log_base,
            self.name,
            self.allow_prefix,
        )


@dataclass(frozen=True)
class Tagged(OpsMixin, ConvertMixin, Expr):
    """An concrete unit expression decorated with a semantic context tag.

    This is used to disambiguate between quantities that share the same
    physical dimension but have different meanings, e.g.,
    geopotential altitude vs. geometric altitude."""

    reference: Expr
    context: Hashable
    """A hashable identifier, e.g. `geopotential`, a tuple of contexts"""

    def __post_init__(self) -> None:
        if isinstance(self.reference, Tagged):
            raise NestingError(
                expr_type=Tagged,
                help=(
                    'use a tuple of contexts instead, "'
                    '"e.g., `context=("airspeed", "true")`.'
                ),
            )

    @property
    def dimension(self) -> Tagged:
        return Tagged(self.reference.dimension, self.context)

    @property
    def kind(self) -> ExpressionKind:
        return self.reference.kind

    def simplify(self) -> Tagged:
        simplified_ref = self.reference.simplify()
        return Tagged(simplified_ref, self.context)


@dataclass(frozen=True)
class QtyKind:
    """An abstract *kind of quantity* (ISO 80000-1) represents a "concept" (e.g.
    speed) *without* a specific unit tied to it.

    When indexed with a unit, it becomes a
    [concrete unit with tagged context][isq.Tagged].
    """

    unit_si: Expr
    """The SI unit, e.g. `M_PERS` for speed"""
    context: Hashable
    """A hashable identifier, e.g. `geopotential`, a tuple of contexts"""

    def __getitem__(self, unit: Expr) -> Tagged:
        """Attach a specific unit to this kind of quantity."""
        if unit is self.unit_si:
            return Tagged(self.unit_si, context=self.context)
        dim_unit = unit.simplify().dimension
        dim_unit_self = self.unit_si.simplify().dimension
        if dim_unit != dim_unit_self:
            raise UnitKindMismatchError(kind=self, unit=unit)
        return Tagged(unit, context=self.context)


def _unwrap_tagged_or_aliased(expr: Expr) -> Expr:
    # `Translated` and `Logarithmic` are terminal, this plugs a loophole
    # NOTE: Alias(Alias(...)) and Tagged(Tagged(...)) is not allowed
    if isinstance(expr, (Tagged, Aliased)):
        return expr.reference
    return expr


#
# simplification
#
def _decompose_expr(
    expr: Expr,  # ‾
    exponent: Exponent,  # *
    base_exponent_pairs_mut: MutableMapping[Expr, Exponent],
    scaled_conversions_mut: MutableSequence[tuple[Scaled, Exponent]],  # ^
) -> None:
    """Recursively traverse an expression tree to flatten it.

    This is the first step of the simplification, example:

    - expr=Mul(Scaled(M, 0.3048, "FT"), Exp(S, -1)), exponent=2
        - expr=Scaled(M, 0.3048, "FT"), exponent=2
            - scaled_conversions_mut += [(Scaled(M, 0.3048, "FT"), 2)]
            - expr=M, exponent=2
                - base_exponent_pairs_mut[M] += 2
        - expr=Exp(S, -1), exponent=2
            - expr=Expr(S, -2), exponent=1
                - base_exponent_pairs_mut[S] += -2
    """
    if isinstance(expr, Aliased):
        _decompose_expr(
            expr.reference,
            exponent,
            base_exponent_pairs_mut,
            scaled_conversions_mut,
        )
    elif isinstance(
        expr,
        (
            Dimensionless,
            BaseDimension,
            BaseUnit,
            Tagged,
            Translated,
            Logarithmic,
        ),
    ):
        # we hit a fundamental-like unit (we treat tagged as unique bases).
        # add its accumulated exponent
        base_exponent_pairs_mut.setdefault(expr, 0)
        base_exponent_pairs_mut[expr] += exponent
    elif isinstance(expr, Exp):
        # (xᵃ)ᵇ -> xᵃᵇ
        # ‾‾‾‾*    ‾**
        _decompose_expr(
            expr.base,
            expr.exponent * exponent,
            base_exponent_pairs_mut,
            scaled_conversions_mut,
        )
    elif isinstance(expr, Mul):
        # (xyᵃ)ᵇ -> xᵇyᵃᵇ
        # ‾‾‾‾‾*    ‾*‾**
        for term in expr.terms:
            _decompose_expr(
                term,
                exponent,
                base_exponent_pairs_mut,
                scaled_conversions_mut,
            )
    elif isinstance(expr, Scaled):
        # (kx)ᵇ -> kᵇxᵇ
        # ‾‾‾‾*    ^^‾*
        scaled_conversions_mut.append((expr, exponent))
        _decompose_expr(
            expr.reference,
            exponent,
            base_exponent_pairs_mut,
            scaled_conversions_mut,
        )
    else:  # pragma: no cover
        raise NotImplementedError(f"unknown {type(expr)=}")


__DIMENSIONLESS_SIMPLIFIED: Final = Dimensionless(name="from_simplified")


def _build_canonical_expr(
    base_exponent_pairs: Mapping[Expr, Exponent],
    scaled_conversions: list[tuple[Scaled, Exponent]],
) -> Expr:
    """Construct a canonical expression from flattened parts.

    This is second step of the simpification. Examples:

    - `{}` and `[]` -> dimensionless
    - `{M: 1}` and `[]` -> `M`
    - `{M: 2}` and `[]` -> `Exp(M, 2)`
    - `{M: 1, S: -2}` and `[]` -> `Mul(M, Exp(S, -2))`
    - `{...}` and `[(Scaled(M, 0.3048, "FT"), 2)]` -> result will be wrapped:
      `Scaled(reference=Mul(..., factor=LazyFactor(...)`
    """
    no_conversions_involved = not scaled_conversions
    simplified_expr: Expr
    # remove zero exponents and ensure canonical order by names
    base_exponent_pairs_sorted = sorted(
        filter(lambda item: item[1] != 0, base_exponent_pairs.items()),
        key=lambda item: str(item[0]),
    )
    if not base_exponent_pairs_sorted:
        simplified_expr = __DIMENSIONLESS_SIMPLIFIED
    elif len(base_exponent_pairs_sorted) == 1:
        base, exponent = base_exponent_pairs_sorted[0]
        simplified_expr = base if exponent == 1 else Exp(base, exponent)
    else:
        simplified_expr = Mul(
            tuple(
                base if exponent == 1 else Exp(base, exponent)
                for base, exponent in base_exponent_pairs_sorted
            )
        )
    if no_conversions_involved:
        return simplified_expr

    return Scaled(
        reference=simplified_expr,
        factor=LazyFactor.from_derived_conversions(scaled_conversions),
    )


#
# unit/dimension conversions
#


@dataclass(frozen=True)
class Converter:
    scale: Factor
    offset: Factor

    @classmethod
    def new(
        cls,
        origin: Expr,
        target: Expr,
        *,
        exact: bool,
        ctx: decimal.Context,
    ) -> Converter:
        """Create a new unit converter from one unit to another.

        Checks that the underlying dimension are compatible
        (e.g. `USD/year` and `HKD/hour`) and computes the total scaling factor.
        """
        origin_simpl = origin.simplify()
        target_simpl = target.simplify()

        info_origin = _flatten(origin_simpl)
        info_target = _flatten(target_simpl)
        origin_core_expr = info_origin.expr
        target_core_expr = info_target.expr
        is_origin_log = isinstance(origin_core_expr, Logarithmic)
        is_target_log = isinstance(target_core_expr, Logarithmic)
        if is_origin_log and is_target_log:
            base_converter = Converter.new_logarithmic(
                origin_core_expr,  # type: ignore
                target_core_expr,  # type: ignore
                exact=exact,
                ctx=ctx,
            )
            # prefixed log units:
            # v_target_prefixed = (scale_base * v_origin_prefixed) + offset_base
            # v_target = (scale_base * factor_origin / factor_target) * v_origin
            #            + (offset_base / factor_target)
            origin_prefix_f = _factor_to_fraction(info_origin.factor, ctx=ctx)
            target_prefix_f = _factor_to_fraction(info_target.factor, ctx=ctx)
            base_scale_f = _factor_to_fraction(base_converter.scale, ctx=ctx)
            base_offset_f = _factor_to_fraction(base_converter.offset, ctx=ctx)

            final_scale = base_scale_f * origin_prefix_f / target_prefix_f
            final_offset = base_offset_f / target_prefix_f
            return cls(
                scale=final_scale if exact else float(final_scale),
                offset=final_offset if exact else float(final_offset),
            )
        elif is_origin_log or is_target_log:
            raise NonLinearConversionError(
                origin=origin,
                target=target,
            )  # e.g. V = V_ref * b**(L_dBV / k), L_dbV = k * log_b(V / V_ref)

        if origin_simpl.kind != target_simpl.kind:
            raise KindMismatchError(
                origin_kind=origin_simpl.kind, target_kind=target_simpl.kind
            )

        origin_dim = info_origin.expr.dimension
        target_dim = info_target.expr.dimension
        origin_dim_terms = (
            origin_dim.terms if isinstance(origin_dim, Mul) else (origin_dim,)
        )
        target_dim_terms = (
            target_dim.terms if isinstance(target_dim, Mul) else (target_dim,)
        )
        if origin_dim_terms != target_dim_terms:
            raise DimensionMismatchError(origin=origin, target=target)
        # we have:
        #   v_abs = scale_origin * v_origin + offset_origin
        #   v_abs = scale_target * v_target + offset_target
        # then:
        #   v_target = (scale_origin / scale_target) * v_origin +
        #              (offset_origin - offset_target) / scale_target
        scale_origin = list(_products(info_origin.factor))

        inv_scale_target = tuple(
            f for f in _products_inverse(info_target.factor)
        )
        scale = LazyFactor(tuple([*scale_origin, *inv_scale_target]))

        offset_numerator = _factor_to_fraction(
            info_origin.offset, ctx=ctx
        ) - _factor_to_fraction(info_target.offset, ctx=ctx)
        offset = LazyFactor(tuple([offset_numerator, *inv_scale_target]))

        return cls(
            scale=scale.to_exact(ctx=ctx) if exact else scale.to_approx(),
            offset=offset.to_exact(ctx=ctx) if exact else offset.to_approx(),
        )

    @classmethod
    def new_logarithmic(
        cls,
        origin_simpl: Logarithmic,
        target_simpl: Logarithmic,
        *,
        exact: bool,
        ctx: decimal.Context,
    ) -> Converter:
        r"""
        With $L_1 = k_1 \log_{b_1}\left(\frac{Q}{Q_{\text{ref}_1}}\right)$,
        $L_2 = k_2 \log_{b_2}\left(\frac{Q}{Q_{\text{ref}_2}}\right)
        = \underbrace{\left(\frac{k_2\ln b_1}{k_1\ln b_2}\right)}_\text{scale}
        L_1 + \underbrace{k_2 \log_{b_2}\left(\frac{Q_{\text{ref}_1}}
        {Q_{\text{ref}_2}}\right)}_\text{offset}$
        """
        origin_ref_dim = origin_simpl.reference.simplify().dimension
        target_ref_dim = target_simpl.reference.simplify().dimension
        if origin_ref_dim != target_ref_dim:  # e.g. dBV -> dBm
            raise DimensionMismatchError(
                origin=origin_simpl.reference, target=target_simpl.reference
            )

        ref_converter = Converter.new(
            origin=origin_simpl.reference,
            target=target_simpl.reference,
            exact=exact,
            ctx=ctx,
        )  # needed for e.g. dBm <-> dBW, dBV <-> dBμV
        ref_ratio = ref_converter.scale  # Q_ref1 / Q_ref2, e.g. W -> mW: 1000

        b1 = origin_simpl.log_base
        b2 = target_simpl.log_base
        k1 = _factor_to_fraction(origin_simpl.level_factor, ctx=ctx)
        k2 = _factor_to_fraction(target_simpl.level_factor, ctx=ctx)
        k_ratio = k2 / k1
        if exact:  # ln is transcendental, tiny precision loss expected
            b1_d = _fraction_to_decimal(_factor_to_fraction(b1, ctx=ctx))
            ln_b2_d = _fraction_to_decimal(_factor_to_fraction(b2, ctx=ctx)).ln(
                ctx
            )
            ln_ref_ratio_d = _fraction_to_decimal(
                _factor_to_fraction(ref_ratio, ctx=ctx)
            ).ln(ctx)
            return cls(
                scale=k_ratio * Fraction(b1_d.ln(ctx)) / Fraction(ln_b2_d),
                offset=k2 * Fraction(ln_ref_ratio_d / ln_b2_d),
            )
        else:
            ln_b2_f = math.log(float(b2))
            return cls(
                scale=float(k_ratio) * math.log(float(b1)) / ln_b2_f,
                offset=float(k2) * (math.log(float(ref_ratio)) / ln_b2_f),
            )

    def __call__(self, value: Any) -> Any:
        """Convert a value in the origin unit to the target unit.

        :param value: An integer, float or [fractions.Fraction][].
            If the converter was created with exact=False, it can also take an
            array-like object.
            If exact=True, [decimal.Decimal][] inputs should be converted into a
            [fractions.Fraction][].
        """
        return value * self.scale + self.offset


class ConversionInfo(NamedTuple):
    expr: Expr
    """Absolute (non-translated, non-scaled) reference"""
    factor: Factor | LazyFactor
    """Total scaling factor to convert from this unit to the absolute reference"""
    offset: Factor | LazyFactor
    """Total offset to convert from this unit to the absolute reference"""


def _flatten(
    expr_simpl: Expr,
) -> ConversionInfo:
    """Recursively flattens an expression into its absolute base unit."""
    if isinstance(
        expr_simpl,
        (BaseUnit, BaseDimension, Dimensionless, Logarithmic, Exp, Mul),
    ):
        # since `Exp(Scaled(x, a), b)` → `Scaled(Exp(x, b), a * b)`
        # similarly, `Mul((Scaled(...),))` → `Scaled(Mul((...),),)`
        return ConversionInfo(expr_simpl, 1, 0)
    elif isinstance(expr_simpl, Scaled):
        # so `Scaled` should always be pushed to outmost level.
        # furthermore, since nested `Scaled(Scaled(x, c), d)` would simplify to
        # `Scaled(x, c * d)`, we don't need to recursively get the factor.
        return ConversionInfo(expr_simpl.reference, expr_simpl.factor, 0)
    elif isinstance(expr_simpl, Tagged):
        info_ref = _flatten(expr_simpl.reference)
        return ConversionInfo(
            Tagged(info_ref.expr, expr_simpl.context),
            info_ref.factor,
            info_ref.offset,
        )
    elif isinstance(expr_simpl, Translated):
        info_ref = _flatten(expr_simpl.reference)
        assert info_ref.offset == 0, (
            f"inner reference of {expr_simpl=} should not have any offset"
        )
        # v_local = v_ref + offset_local
        #   v_abs = v_ref * factor_ref
        #         = v_local * factor_ref - offset_local * factor_ref
        new_offset = LazyFactor(
            (-1, expr_simpl.offset, *_products(info_ref.factor))
        )
        return ConversionInfo(info_ref.expr, info_ref.factor, new_offset)
    else:  # pragma: no cover, NOTE: Alias should be simplified away
        raise NotImplementedError(f"unknown expression {expr_simpl}")


def _products(
    factor: Factor | LazyFactor,
) -> Generator[tuple[Factor, Exponent] | Factor]:
    if isinstance(factor, LazyFactor):
        for product in factor.products:
            yield product
    else:
        yield factor


def _products_inverse(
    factor: Factor | LazyFactor,
) -> Generator[tuple[Factor, Exponent] | Factor]:
    for item in _products(factor):
        if isinstance(item, tuple):
            base, exponent = item
            yield (base, -exponent)
        else:
            yield (item, -1)


def _factor_to_fraction(
    factor: Factor | LazyFactor, *, ctx: decimal.Context
) -> Fraction:
    if isinstance(factor, LazyFactor):
        return Fraction(factor.to_exact(ctx=ctx))
    elif isinstance(factor, (Decimal, float, int)):
        return Fraction(factor)
    elif isinstance(factor, SupportsDecimal):
        return Fraction(factor.to_decimal(ctx=ctx))
    elif not isinstance(factor, Fraction):
        raise NotImplementedError(
            f"unknown {type(factor)=}"
        )  # pragma: no cover
    return factor


def _fraction_to_decimal(fraction: Fraction) -> Decimal:
    return fraction.numerator / Decimal(fraction.denominator)


@dataclass(frozen=True)
class LazyFactor(SupportsFloat):
    """Represents a scaling factor as a sequence of products.

    Lazy evaluation allows the choice between evaluating it to an exact value
    (taking longer to compute, useful for financial calculations) or an
    approximate float.
    """

    products: tuple[tuple[Factor, Exponent] | Factor, ...]

    @classmethod
    def from_derived_conversions(
        cls,
        derived_conversions: Sequence[tuple[Scaled, Exponent]],
    ) -> LazyFactor:
        products: list[tuple[Factor, Exponent] | Factor] = []
        for scaled, exponent in derived_conversions:
            for inner_item in _products(scaled.factor):
                if isinstance(inner_item, tuple):
                    base, inner_exp = inner_item
                    products.append((base, inner_exp * exponent))
                else:
                    products.append((inner_item, exponent))
        return cls(tuple(products))

    def to_approx(self) -> float:
        """Reduce it to an approximate float value. Good enough for most
        applications."""
        product = 1.0
        for item in self.products:
            base, exponent = item if isinstance(item, tuple) else (item, 1)
            if base == 0:
                if exponent > 0:
                    return 0.0
                if exponent == 0:
                    continue  # 0 ** 0 = 1
            if base == 1:
                continue
            product *= float(base) ** float(exponent)
        return product

    # NOTE: not defining `__mul__` to avoid confusion.
    def __float__(self) -> float:
        return self.to_approx()

    def to_exact(
        self, *, ctx: decimal.Context | None = None
    ) -> Fraction | Decimal:
        """Reduce it to an *exact* fraction or decimal.

        :param ctx: The decimal context (precision, rounding, etc.) to use.
            If none, the global `decimal.getcontext()` is used.

        The return type depends on the items of each product:

        ```
                         +--------+-------+----------------+
                         |  None  |  int  | Fraction(p, q) | <- exponent
        +----------------+--------+-------+----------------+
        | Decimal        |   .    |   .   |       x        |
        | Fraction(a, b) |   .    |   .   |       *        |
        | float          |   .    |   x   |       x        |
        | int            |   .    |   .   |       ^        |
        +----------------+--------+-------+----------------+
          ^
          |_ base

        Can `base ** exponent` be represented exactly a `Fraction`?

        . Yes
        * Only if q > 0 and a^p and b^q are the perfect q-th power of an integer
          e.g. (8/27) ** (1/3) = 2/3
        ^ Sometimes, e.g. 4 ** (1/2)
        x No, decimal only
        ```

        For simplicity, only cases that can definitively be represented as a
        `Fraction` are returned as such. A `Decimal` is returned otherwise.
        """
        ctx = ctx or decimal.getcontext()
        # accumulate products in two streams: if the "tripwire" for decimal
        # is hit, we must return Decimal.
        product_fraction = Fraction(1)
        product_decimal = Decimal(1)
        for item in self.products:
            if not isinstance(item, tuple):  # no exponent
                product_fraction *= _factor_to_fraction(item, ctx=ctx)
                continue
            base, exponent = item
            if base == 0:
                if exponent > 0:
                    return Fraction(0)
                if exponent < 0:
                    raise ZeroDivisionError
                continue  # 0 ** 0 = 1
            if base == 1:
                continue
            if isinstance(exponent, int):
                # most of the time, we can represent it as Fraction
                if isinstance(base, float):
                    base_decimal = ctx.create_decimal_from_float(base)
                    product_decimal *= base_decimal**exponent
                else:
                    base_fraction = _factor_to_fraction(base, ctx=ctx)
                    product_fraction *= base_fraction**exponent
            elif isinstance(exponent, Fraction):
                # but raising to a Fraction exponent requires decimal
                if isinstance(base, Decimal):
                    base_decimal = base
                elif isinstance(base, Fraction):  # *
                    base_decimal = _fraction_to_decimal(base)
                elif isinstance(base, float):
                    base_decimal = ctx.create_decimal_from_float(base)
                elif isinstance(base, int):  # ^
                    base_decimal = Decimal(base, context=ctx)
                else:  # pragma: no cover
                    raise NotImplementedError(f"unknown {type(base)=}")
                exponent_decimal = _fraction_to_decimal(exponent)
                product_decimal *= ctx.power(base_decimal, exponent_decimal)
            else:  # pragma: no cover
                raise NotImplementedError(f"unknown {type(exponent)=}")
        if product_decimal == Decimal(1):
            return product_fraction
        return _fraction_to_decimal(product_fraction) * product_decimal


@final
class _E(SupportsDecimal):
    __slots__ = ()

    def to_decimal(self, ctx: decimal.Context) -> Decimal:
        return ctx.exp(Decimal(1))

    def __float__(self) -> float:
        return math.e


@final
class _PI(SupportsDecimal):
    __slots__ = ()

    def to_decimal(self, ctx: decimal.Context) -> Decimal:
        # from: https://docs.python.org/3/library/decimal.html#recipes
        ctx.prec += 2  # extra digits for intermediate steps
        three = Decimal(3)
        lasts, t, s, n, na, d, da = Decimal(0), three, Decimal(3), 1, 0, 0, 24
        while s != lasts:
            lasts = s
            n, na = n + na, na + 8
            d, da = d + da, da + 32
            t = (t * n) / d
            s += t
        ctx.prec -= 2
        pi = +s  # unary plus applies the new precision
        return pi

    def __float__(self) -> float:
        return math.pi


E: Final = _E()
PI: Final = _PI()

#
# errors
#


class IsqError(Exception):
    """Base exception for all errors raised by the isq library."""


# structural
@dataclass
class TerminalUnitError(IsqError):
    expr: Expr
    op: type[Exp] | type[Mul] | type[Scaled]
    help: str | None = None
    note: str | None = None

    def __str__(self) -> str:  # pragma: no cover
        if self.op is Exp:
            op_name = "exponentiation"
        elif self.op is Mul:
            op_name = "multiplication"
        elif self.op is Scaled:
            op_name = "scaling"
        else:
            raise NotImplementedError
        message = (
            f"cannot perform {op_name} on terminal expression `{self.expr}`."
            f"\nnote: `{type(self.expr).__name__}` expressions are final and "
            "cannot be composed further."
        )
        if self.help:
            message += f"\nhelp: {self.help}"
        if self.note:
            message += f"\nnote: {self.note}"
        return message


@dataclass
class ReferenceTypeError(IsqError):
    expr_type: type[Expr]
    ref: Expr
    allowed_types_msg: str
    note: str | None = None

    def __str__(self) -> str:  # pragma: no cover
        message = (
            f"invalid reference for `{self.expr_type.__name__}`."
            f"\n     got: `{self.ref}` (of type `{type(self.ref).__name__}`)"
            f"\nexpected: {self.allowed_types_msg}"
        )
        if self.note:
            message += f"\nnote: {self.note}"
        return message


@dataclass
class NestingError(IsqError):
    expr_type: type[Expr]
    help: str | None = None

    def __str__(self) -> str:  # pragma: no cover
        message = (
            f"nesting `{self.expr_type.__name__}` expressions is not allowed."
        )
        if self.help:
            message += f"\nhelp: {self.help}"
        return message


@dataclass
class PrefixError(IsqError):
    prefix: Prefix
    target: BaseUnit | Aliased | Logarithmic
    note: str

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"cannot apply prefix `{self.prefix.name}` to `{self.target.name}`."
            f"\nnote: {self.note}"
        )


@dataclass
class MixedKindError(IsqError):
    terms: tuple[Expr, ...]

    def __str__(self) -> str:  # pragma: no cover
        return (
            "cannot mix expressions of different kinds in a product."
            f"\n  found kinds: {', '.join(f'`{t.kind}`' for t in self.terms)}"
            "\nhelp: all terms in a `Mul` expression must be of the same kind "
            "(e.g., all units like `M` and `S`, or all dimensions like "
            "`DIM_LENGTH` and `DIM_TIME`)."
        )


@dataclass
class CompositionError(IsqError):
    msg: str
    help: str | None = None

    def __str__(self) -> str:  # pragma: no cover
        message = self.msg
        if self.help:
            message += f"\nhelp: {self.help}"
        return message


# conversion
@dataclass
class KindMismatchError(IsqError):
    origin_kind: ExpressionKind
    target_kind: ExpressionKind

    def __str__(self) -> str:  # pragma: no cover
        return (
            "cannot convert between expressions of different kinds."
            f"\nnote: origin kind: `{self.origin_kind}`"
            f"\n      target kind: `{self.target_kind}`"
        )


@dataclass
class DimensionMismatchError(IsqError):
    origin: Expr
    target: Expr

    def __str__(self) -> str:  # pragma: no cover
        origin_dim = self.origin.simplify().dimension
        target_dim = self.target.simplify().dimension
        return (
            f"cannot convert from `{self.origin}` to `{self.target}` due to "
            "incompatible dimensions."
            f"\ndimension of origin: `{origin_dim}`"
            f"\ndimension of target: `{target_dim}`"
        )


@dataclass
class UnitKindMismatchError(IsqError):
    kind: QtyKind
    unit: Expr

    def __str__(self) -> str:  # pragma: no cover
        kind_dim = self.kind.unit_si.simplify().dimension
        unit_dim = self.unit.simplify().dimension
        return (
            f"cannot create tagged unit for kind `{self.kind.context}` with "
            f"unit `{self.unit}`."
            f"\nexpected kind dimension: `{kind_dim}` (`{self.kind.unit_si}`)"
            f"\n   found unit dimension: `{unit_dim}` (`{self.unit}`)"
        )


@dataclass
class NonLinearConversionError(IsqError):
    origin: Expr
    target: Expr

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"cannot create a value-agnostic converter from `{self.origin}` "
            f"to `{self.target}`."
            "conversion between a logarithmic and a linear unit is non-linear."
            "\nhelp: this requires a reference value (e.g., 1V for dBV), "
            "but this library only performs value-agnostic conversions. "
            "please perform the calculation manually."
        )


# NOTE: for a registry, one option is to adopt https://peps.python.org/pep-0487/#subclass-registration:
# - have a `Registrable` mixin with `__init_subclass__` so the act of defining a class `S` automatically adds it to a global dict
# - this guarantees completeness with zero boilerplate
# - BUT... importing a module containing units would have side effects. explicit registration is prob a better idea
# - we need to be careful of circular imports (avoid importing ft before m)
