from __future__ import annotations

import decimal
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import (
    TYPE_CHECKING,
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
    SupportsAbs,
    SupportsFloat,
    Union,
    final,
    overload,
    runtime_checkable,
)

from typing_extensions import TypeAlias, assert_never

if TYPE_CHECKING:
    from .fmt import _FormatSpec, _Formatter


@runtime_checkable
class SupportsDecimal(SupportsFloat, SupportsAbs[object], Protocol):
    def to_decimal(self, ctx: decimal.Context) -> Decimal: ...


ExprKind: TypeAlias = Literal["dimensionless", "unit", "dimension"]
Number: TypeAlias = Union[SupportsDecimal, Decimal, Fraction, float, int]
Name: TypeAlias = str
"""A unique slug to identify the expression. This is used by the default basic
formatter to display the expression and hence should not contain any spaces
to avoid ambiguity. For example, `meter`, `newton`, `reynolds`"""


@runtime_checkable
class Named(Protocol):
    name: Name


# NOTE: these mixins are separate from ExprBase because:
# - the `Alias` expression cannot wrap itself
# - all expressions are formattable, but in the future we also want `QtyKind`
#   (not an ExprBase) to be formattable.


class AliasMixin:
    def alias(self, name: Name, *, allow_prefix: bool = False) -> Aliased:
        """Wrap this expression with a name.

        :param name: Name of this alias, e.g. `newton`
        :param allow_prefix: Whether to allow [prefixes][isq.Prefix] to be
        attached. This should only be true for some units like `liter`
        """
        return Aliased(self, name=name, allow_prefix=allow_prefix)  # type: ignore


class FormatMixin:
    def __format__(self, fmt: _FormatSpec | str | _Formatter) -> str:
        from .fmt import fmt as format_

        return format_(self, fmt=fmt)  # type: ignore

    def __str__(self) -> str:
        return self.__format__("basic")


class ExprBase(ABC, FormatMixin):
    """A base class for a "unit-like" expression.

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

    Operator overloading is provided for ergonomic expression construction.

    !!! note
        While dividing expressions is supported, it is strongly discouraged as
        it can lead to operator precedence ambiguity. For example, while Python
        interprets `J / KG / K` as `(J / KG) / K`, it is often clearer to
        represent it as `J * KG**-1 * K**-1`.
    """

    @property
    @abstractmethod
    def dimension(self) -> Expr:
        """Return the dimension of this "unit-like" expression.
        Note that it does not perform simplification.

        Examples:

        - `Exp(M, 2)` -> `Exp(DIM_LENGTH, 2)`
        - `Mul(M, Exp(S, -1))` -> `Mul(DIM_LENGTH, Exp(DIM_TIME, -1))`
        """
        ...

    @property
    @abstractmethod
    def kind(self) -> ExprKind:
        """Whether this expression is a unit, dimension, or dimensionless."""
        ...

    def __pow__(self, exponent: Exponent) -> Exp:
        return Exp(self, exponent)  # type: ignore

    @overload
    def __mul__(self, rhs: Expr) -> Mul: ...

    @overload
    def __mul__(self, rhs: LazyProduct | Number) -> Scaled: ...

    # NOTE: not allowing Prefix as rhs to avoid confusion
    def __mul__(self, rhs: Expr | LazyProduct | Number) -> Mul | Scaled:
        if isinstance(
            rhs, (LazyProduct, SupportsDecimal, Decimal, Fraction, float, int)
        ):
            return Scaled(self, rhs)  # type: ignore
        # make sure KG * M * S becomes flat, not Mul((Mul((KG, M)), S))
        terms_self = self.terms if isinstance(self, Mul) else (self,)
        terms_other = rhs.terms if isinstance(rhs, Mul) else (rhs,)
        return Mul(tuple([*terms_self, *terms_other]))

    def __rmul__(self, lhs: LazyProduct | Number | Prefix) -> Scaled:
        if isinstance(lhs, Prefix):
            return lhs.mul(self)  # type: ignore
        return Scaled(self, lhs)  # type: ignore

    @overload
    def __truediv__(self, rhs: Expr) -> Mul: ...

    @overload
    def __truediv__(self, rhs: LazyProduct | Number) -> Scaled: ...

    def __truediv__(self, rhs: Expr | LazyProduct | Number) -> Mul | Scaled:
        if isinstance(rhs, Expr):  # type: ignore
            return self * rhs**-1  # type: ignore

        return Scaled(
            self,  # type: ignore
            LazyProduct(tuple(f for f in _products_inverse(rhs))),  # type: ignore
        )  # M / 2 => Scaled(M, Fraction(1, 2))


@dataclass(frozen=True)
class Dimensionless(Named, ExprBase):
    name: Name
    """Name for the dimensionless number, e.g. `reynolds`, `prandtl`"""

    @property
    def dimension(self) -> Dimensionless:
        return self

    @property
    def kind(self) -> ExprKind:
        return "dimensionless"


@dataclass(frozen=True)
class BaseDimension(Named, ExprBase):
    name: Name
    """Name for the base dimension, e.g. `L`, `M`, `T`"""

    @property
    def dimension(self) -> BaseDimension:
        return self

    @property
    def kind(self) -> ExprKind:
        return "dimension"


@dataclass(frozen=True)
class BaseUnit(Named, ExprBase):
    _dimension: BaseDimension
    """Reference to the base dimension"""
    name: Name
    """Name for the unit, e.g. `m`, `kg`, `s`"""

    @property
    def dimension(self) -> BaseDimension:
        return self._dimension

    @property
    def kind(self) -> ExprKind:
        return "unit"


Exponent: TypeAlias = Union[int, Fraction]
"""An exponent, generally small integers, which can be positive, negative,
or a fraction, but not zero"""


@dataclass(frozen=True)
class Exp(AliasMixin, ExprBase):
    """An expression raised to an exponent.
    For example, `BaseUnit("meter", Dimension("L")), 2)` is m².
    Can be recursively nested, e.g. `Exp(Exp(METER, 2), Fraction(1, 2))`
    """

    base: _ComposableExpr
    exponent: Exponent
    """Exponent. Avoid using zero to represent dimensionless numbers: 
    use [isq.Dimensionless][] with a name instead."""

    def __post_init__(self) -> None:
        if not isinstance(self.exponent, (int, Fraction)):
            raise CompositionError(
                outer=Exp,
                inner=self.exponent,
                msg=(
                    "exponent must be an integer or a fraction, "
                    f"not {type(self.exponent).__name__}."
                ),
            )
        if self.exponent == 0:
            raise CompositionError(
                outer=Exp,
                inner=self.exponent,
                msg="exponent must not be zero.",
                help="use `Dimensionless` to represent a dimensionless quantity.",
            )
        ref = _unwrap_tagged_or_aliased(self.base)
        if isinstance(ref, Translated):
            raise CompositionError(
                outer=Exp,
                inner=ref,
                msg="translated units (like ℃) are terminal and cannot be exponentiated.",
                help=(
                    "did you mean to exponentiate its "
                    f"absolute reference `{ref.reference}` instead?"
                ),
            )  # prevent ℃². J ℃⁻¹ should be written as J K⁻¹
        elif isinstance(ref, Logarithmic):
            raise CompositionError(
                outer=Exp,
                inner=ref,
                msg="logarithmic units are terminal and cannot be raised to a power.",
            )

    @property
    def dimension(self) -> Exp:
        return Exp(self.base.dimension, self.exponent)  # type: ignore

    @property
    def kind(self) -> ExprKind:
        return self.base.kind


@dataclass(frozen=True)
class Mul(AliasMixin, ExprBase):
    """Products of powers of an expression."""

    terms: tuple[_ComposableExpr, ...]
    """A tuple of expressions to be multiplied, preserving the order."""

    def __post_init__(self) -> None:
        if not self.terms:
            raise CompositionError(
                outer=Mul,
                inner=self.terms,
                msg="`Mul` terms must not be empty.",
                help="use `Dimensionless` to represent a dimensionless quantity.",
            )
        kinds = []
        for term in self.terms:
            ref = _unwrap_tagged_or_aliased(term)
            if isinstance(ref, Translated):
                raise CompositionError(
                    outer=Mul,
                    inner=ref,
                    msg="`Translated` units (like ℃) are terminal and cannot be part of a product.",
                    help=f"use its absolute reference `{ref.reference}` instead.",
                )  # prevent ℃ * ℃
            elif isinstance(ref, Logarithmic):
                raise CompositionError(
                    outer=Mul,
                    inner=ref,
                    msg="`Logarithmic` units are terminal and cannot be part of a product.",
                )
            kinds.append(term.kind)
        unique_kinds = set(kinds) - {"dimensionless"}
        if len(unique_kinds) != 1:
            raise MixedKindError(terms=self.terms)

    @property
    def dimension(self) -> Mul:
        return Mul(tuple(term.dimension for term in self.terms))  # type: ignore

    @property
    def kind(self) -> ExprKind:
        # all terms have a consistent underlying kind (unit/dimension)
        for term in self.terms:
            term_kind = term.kind
            if term_kind != "dimensionless":
                return term_kind
        # everything left are dimensionless to the power of something
        return "dimensionless"


@dataclass(frozen=True)
class Scaled(AliasMixin, ExprBase):
    reference: BaseUnit | Exp | Mul | Scaled | Aliased | Tagged | Logarithmic
    """The unit or dimension that this unit or dimension is based on."""
    factor: Number | LazyProduct | Prefix
    """The exact factor to multiply to this unit to convert it to the reference.
    For example, `1 ft = 0.3048 m`, so the factor is 0.3048.
    """

    def __post_init__(self) -> None:
        if not isinstance(
            self.factor,
            (
                LazyProduct,
                SupportsDecimal,
                Decimal,
                Fraction,
                float,
                int,
                Prefix,
            ),
        ):
            raise CompositionError(
                outer=Scaled,
                inner=self.factor,
                msg=f"factor must be a number, not {type(self.factor).__name__}.",
            )
        ref = _unwrap_tagged_or_aliased(self.reference)
        if isinstance(ref, Translated) or (
            isinstance(ref, Logarithmic) and not ref.allow_prefix
        ):
            raise CompositionError(
                outer=Scaled,
                inner=self.reference,
                msg=(
                    "`Translated` units (like ℃) and most logarithmic units "
                    "(like dBV) cannot be scaled."
                ),
            )  # prevent 13 * ℃, milli(decibel)
        # TODO: prevent BaseDimension and Dimensionless from being scaled

    @property
    def dimension(self) -> Expr:
        return self.reference.dimension

    @property
    def kind(self) -> ExprKind:
        return self.reference.kind


@dataclass(frozen=True)
class Aliased(Named, ExprBase):
    """An alias for an expression, used to give a more readable name.

    Note that unlike a [tagged][isq.Tagged] expression,
    [simplification][isq.simplify] will effectively elide this class.
    """

    reference: Exp | Mul | Scaled
    """Expression to be aliased, e.g. `Mul((KG, M, Exp(S, -2)))`"""
    name: Name
    """Name of this alias, e.g. `newton`"""
    allow_prefix: bool = False
    """Whether to allow [prefixes][isq.Prefix] to be attached.
    This should only be true for some units like `liter`."""

    def __post_init__(self) -> None:
        ref = self.reference
        if not isinstance(self.reference, (Exp, Mul, Scaled)):
            raise CompositionError(
                outer=Aliased,
                inner=ref,
                msg="`Aliased` can only wrap an `Exp`, `Mul`, or `Scaled` expression.",
            )

    @property
    def dimension(self) -> Expr:
        return self.reference.dimension

    @property
    def kind(self) -> ExprKind:
        return self.reference.kind


@dataclass(frozen=True)
class Translated(Named, ExprBase):
    """An expression offsetted from some reference unit."""

    reference: BaseUnit | Scaled | Aliased | Tagged
    """The expression that this expression is based on (e.g., `K` for `DEGC`)"""
    offset: Number
    """The exact offset to add to the reference to get this unit.
    For example, `℃ = K - 273.15`, so the offset is -273.15."""
    name: Name

    def __post_init__(self) -> None:
        ref = _unwrap_tagged_or_aliased(self.reference)
        if isinstance(ref, Translated):
            raise CompositionError(
                outer=Translated,
                inner=ref,
                msg="nesting `Translated` expressions is not allowed.",
            )
        if not isinstance(ref, (BaseUnit, Scaled)):
            raise CompositionError(
                outer=Translated,
                inner=ref,
                msg="`Translated` must have a `BaseUnit` or `Scaled` expression as its reference.",
            )

    @property
    def kind(self) -> ExprKind:
        return self.reference.kind

    @property
    def dimension(self) -> Expr:
        return self.reference.dimension


@dataclass(frozen=True)
class Logarithmic(Named, ExprBase):
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

    reference: BaseUnit | Exp | Mul | Scaled | Aliased | Tagged
    """The linear unit being measured (e.g., V for dBV, W for dBm)"""
    quantity_type: Literal["power", "field"]
    """Whether the reference is a power or a field quantity."""
    log_base: Number
    """The base of the logarithm (e.g., 10, 2, [isq.E][])"""
    name: Name
    allow_prefix: bool = False
    """Whether prefixes can be applied to the logarithmic unit (e.g., mNp)."""

    def __post_init__(self) -> None:
        ref = _unwrap_tagged_or_aliased(self.reference)
        if isinstance(ref, (Logarithmic, Translated)):
            raise CompositionError(
                outer=Logarithmic,
                inner=ref,
                msg="reference for a `Logarithmic` cannot be logarithmic or translated.",
                help="it must be a linear unit (e.g. `V`, `W`).",
            )
        if ref.kind != "unit":
            raise CompositionError(
                outer=Logarithmic,
                inner=ref,
                msg=f"reference must be a physical unit, not a `{ref.kind}`.",
                help="a logarithmic unit must be based on a quantity with a physical unit.",
            )

    @property
    def level_factor(self) -> Number:
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


@dataclass(frozen=True)
class Tagged(ExprBase):
    """An concrete unit expression decorated with a semantic context tag.

    This is used to disambiguate between quantities that share the same
    physical dimension but have different meanings, e.g.,
    geopotential altitude vs. geometric altitude."""

    reference: _TaggedAllowedExpr
    context: tuple[Hashable, ...]
    """A tuple of hashable tags, e.g. `("alt", "geopotential")`."""

    def __post_init__(self) -> None:
        if isinstance(self.reference, Tagged):
            raise CompositionError(
                outer=Tagged,
                inner=self.reference,
                msg="nesting `Tagged` expressions is not allowed.",
                help='use a tuple of contexts instead, e.g. `("alt", "geopotential")`.',
            )

    @property
    def dimension(self) -> Tagged:
        return Tagged(self.reference.dimension, self.context)  # type: ignore

    @property
    def kind(self) -> ExprKind:
        return self.reference.kind


# using sealed unions instead of ExprBase to facilitate static type checking
Expr: TypeAlias = Union[
    Dimensionless,
    BaseDimension,
    BaseUnit,
    Exp,
    Mul,
    Scaled,
    Aliased,
    Translated,
    Logarithmic,
    Tagged,
]
NamedExpr: TypeAlias = Union[
    Dimensionless, BaseDimension, BaseUnit, Aliased, Translated, Logarithmic
]
_TaggedAllowedExpr: TypeAlias = Union[
    Dimensionless,
    BaseDimension,
    BaseUnit,
    Exp,
    Mul,
    Scaled,
    Aliased,
    Translated,
    Logarithmic,  # e.g. dB(A)
]  # avoid nesting tags
_ComposableExpr: TypeAlias = Union[
    Dimensionless, BaseDimension, BaseUnit, Exp, Mul, Scaled, Aliased, Tagged
]  # avoid terminal (translated/logarithmic) from being further composed

#
# factories for expressions
#


@dataclass(frozen=True)
class Prefix:
    """A prefix, which when multiplied by a [base unit][isq.BaseUnit] or
    [aliased unit][isq.Aliased], returns a [scaled unit][isq.Scaled].

    Note that this is not an [isq.Expr][].
    """

    value: Number
    name: str
    """Name of this prefix, e.g. `milli`, `kibi`"""

    def mul(self, rhs: BaseUnit | Aliased | Tagged | Logarithmic) -> Scaled:
        if not isinstance(rhs, (BaseUnit, Aliased, Tagged, Logarithmic)):
            raise CompositionError(
                outer=Scaled,
                inner=rhs,
                msg=f"prefixes cannot be applied to `{type(rhs).__name__}`.",
            )  # this will prevent double prefixing

        if isinstance(rhs, BaseUnit):
            if rhs.name == "kilogram":
                raise CompositionError(
                    outer=Scaled,
                    inner=rhs,
                    msg="cannot prefix `kilogram`.",
                    help="apply the prefix to `gram` instead.",
                )
        elif isinstance(rhs, Aliased):
            if not rhs.allow_prefix:
                raise CompositionError(
                    outer=Scaled,
                    inner=rhs,
                    msg=f"The aliased unit `{rhs.name}` does not allow prefixes.",
                )
            if self.name == "kilo" and rhs.name == "gram":
                raise CompositionError(
                    outer=Scaled,
                    inner=rhs,
                    msg="cannot apply prefix `kilo` to `gram`.",
                    help="use the `KG` unit directly.",
                )
        elif isinstance(rhs, Tagged) and not isinstance(
            (ref := _unwrap_tagged_or_aliased(rhs)),
            (BaseUnit, Aliased, Logarithmic),
        ):
            raise CompositionError(
                outer=Scaled,
                inner=rhs,
                msg="prefixes cannot be applied to this type of tagged expression.",
                help=f"the inner reference is `{type(ref).__name__}`, which cannot be prefixed.",
            )
        elif isinstance(rhs, Logarithmic):
            if not rhs.allow_prefix:
                raise CompositionError(
                    outer=Scaled,
                    inner=rhs,
                    msg=f"the logarithmic unit `{rhs.name}` does not allow prefixes.",
                )
        return Scaled(rhs, self)


@dataclass(frozen=True)
class QtyKind:
    """An abstract *kind of quantity* (ISO 80000-1) represents a "concept" (e.g.
    speed) *without* a specific unit tied to it.

    When indexed with a unit, it becomes a
    [concrete unit with tagged context][isq.Tagged].
    """

    unit_si: _TaggedAllowedExpr
    """The SI unit, e.g. `M_PERS` for speed"""
    context: tuple[Hashable, ...]
    """A tuple of hashable tags, e.g. `("alt", "geopotential")`."""

    def __getitem__(self, unit: _TaggedAllowedExpr) -> Tagged:
        """Attach a specific unit to this kind of quantity."""
        if unit is self.unit_si:
            return Tagged(self.unit_si, context=self.context)

        dim_unit = simplify(unit).dimension
        dim_unit_self = simplify(self.unit_si).dimension
        if dim_unit != dim_unit_self:
            raise UnitKindMismatchError(self, unit, dim_unit_self, dim_unit)
        return Tagged(unit, context=self.context)


SimplifiedExpr: TypeAlias = Union[
    Dimensionless,
    BaseDimension,
    BaseUnit,
    Exp,
    Mul,
    Scaled,
    Translated,
    Logarithmic,
    Tagged,
]  # no Aliased

#
# simplify
#
# TODO: in the future, we want a as_basis() function that accepts set[Expr]
# why: we sometimes want to re-express some unit not in MKS, but CGS.
# that will require linear algebra to solve the dimensional exponents but
# we're leaving that as optional and far in the future.


@overload
def simplify(expr: Dimensionless) -> Dimensionless: ...
@overload
def simplify(expr: BaseDimension) -> BaseDimension: ...
@overload
def simplify(expr: BaseUnit) -> BaseUnit: ...
@overload
def simplify(expr: Translated) -> Translated: ...
@overload
def simplify(expr: Aliased) -> SimplifiedExpr: ...
@overload
def simplify(expr: Logarithmic) -> Logarithmic: ...
@overload
def simplify(expr: Tagged) -> Tagged: ...
@overload
def simplify(
    expr: Exp | Mul | Scaled,
) -> Union[
    Dimensionless,
    BaseDimension,
    BaseUnit,
    Exp,
    Mul,
    Scaled,
    Translated,
    Logarithmic,
]: ...


# TODO: Expr is too wide: alias should never be returned.
def simplify(expr: Expr) -> SimplifiedExpr:
    if isinstance(expr, (Dimensionless, BaseDimension, BaseUnit)):
        return expr
    if isinstance(expr, Aliased):
        return simplify(expr.reference)
    if isinstance(expr, Translated):
        return Translated(
            simplify(expr.reference),  # type: ignore
            expr.offset,
            expr.name,
        )
    if isinstance(expr, Logarithmic):
        return Logarithmic(
            simplify(expr.reference),  # type: ignore
            expr.quantity_type,
            expr.log_base,
            expr.name,
            expr.allow_prefix,
        )
    if isinstance(expr, Tagged):
        return Tagged(simplify(expr.reference), expr.context)  # type: ignore
    base_exponent_pairs: dict[SimplifiedExpr, Exponent] = {}
    scaled_conversions: list[tuple[Scaled, Exponent]] = []
    _decompose_expr(expr, 1, base_exponent_pairs, scaled_conversions)
    return _build_canonical_expr(base_exponent_pairs, scaled_conversions)


# migrate to pattern matching when we drop support for py3.9
def _decompose_expr(
    expr: Expr,  # ‾
    exponent: Exponent,  # *
    base_exponent_pairs_mut: MutableMapping[SimplifiedExpr, Exponent],
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
        assert_never(expr)


__DIMENSIONLESS_SIMPLIFIED: Final = Dimensionless(name="from_simplified")


def _build_canonical_expr(
    base_exponent_pairs: Mapping[SimplifiedExpr, Exponent],
    scaled_conversions: list[tuple[Scaled, Exponent]],
) -> SimplifiedExpr:
    """Construct a canonical expression from flattened parts.

    This is second step of the simpification. Examples:

    - `{}` and `[]` -> dimensionless
    - `{M: 1}` and `[]` -> `M`
    - `{M: 2}` and `[]` -> `Exp(M, 2)`
    - `{M: 1, S: -2}` and `[]` -> `Mul(M, Exp(S, -2))`
    - `{...}` and `[(Scaled(M, 0.3048, "FT"), 2)]` -> result will be wrapped:
      `Scaled(reference=Mul(..., factor=LazyProduct(...)`
    """
    no_conversions_involved = not scaled_conversions
    simplified_expr: Expr
    # remove zero exponents and ensure canonical order by names
    base_exponent_pairs_sorted = sorted(
        filter(lambda item: item[1] != 0, base_exponent_pairs.items()),
        key=lambda item: repr(item[0]),
    )
    if not base_exponent_pairs_sorted:
        simplified_expr = __DIMENSIONLESS_SIMPLIFIED
    elif len(base_exponent_pairs_sorted) == 1:
        base, exponent = base_exponent_pairs_sorted[0]
        simplified_expr = base if exponent == 1 else Exp(base, exponent)  # type: ignore
    else:
        simplified_expr = Mul(
            tuple(
                base if exponent == 1 else Exp(base, exponent)  # type: ignore
                for base, exponent in base_exponent_pairs_sorted
            )
        )
    if no_conversions_involved:
        return simplified_expr

    return Scaled(
        reference=simplified_expr,  # type: ignore
        factor=LazyProduct.from_derived_conversions(scaled_conversions),
    )


#
# converter
#


@dataclass(frozen=True)
class Converter:
    scale: Number
    offset: Number

    def __call__(self, value: Any) -> Any:
        """Convert a value in the origin unit to the target unit.

        :param value: An integer, float or [fractions.Fraction][].
            If the converter was created with exact=False, it can also take an
            array-like object.
            If exact=True, [decimal.Decimal][] inputs should be converted into a
            [fractions.Fraction][].
        """
        return value * self.scale + self.offset


def convert(
    origin: Expr,
    target: Expr,
    *,
    exact: bool = False,
    ctx: decimal.Context | None = None,
) -> Converter:
    """Create a new unit converter from one unit to another.

    Checks that the underlying dimension are compatible
    (e.g. `USD/year` and `HKD/hour`) and computes the total scaling factor.
    """
    ctx = ctx or decimal.getcontext()
    origin_simpl = simplify(origin)
    target_simpl = simplify(target)

    info_origin = _flatten(origin_simpl)
    info_target = _flatten(target_simpl)
    origin_core_expr = info_origin.expr
    target_core_expr = info_target.expr
    is_origin_log = isinstance(origin_core_expr, Logarithmic)
    is_target_log = isinstance(target_core_expr, Logarithmic)
    if is_origin_log and is_target_log:
        # NOTE: convert_logarithmic calls convert again, which is not ideal for
        # performance.
        base_converter = _convert_logarithmic(
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
        return Converter(
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
        raise DimensionMismatchError(origin, target, origin_dim, target_dim)
    # we have:
    #   v_abs = scale_origin * v_origin + offset_origin
    #   v_abs = scale_target * v_target + offset_target
    # then:
    #   v_target = (scale_origin / scale_target) * v_origin +
    #              (offset_origin - offset_target) / scale_target
    scale_origin = list(_products(info_origin.factor))

    inv_scale_target = tuple(f for f in _products_inverse(info_target.factor))
    scale = LazyProduct(tuple([*scale_origin, *inv_scale_target]))

    offset_numerator = _factor_to_fraction(
        info_origin.offset, ctx=ctx
    ) - _factor_to_fraction(info_target.offset, ctx=ctx)
    offset = LazyProduct(tuple([offset_numerator, *inv_scale_target]))

    return Converter(
        scale=scale.to_exact(ctx=ctx) if exact else scale.to_approx(),
        offset=offset.to_exact(ctx=ctx) if exact else offset.to_approx(),
    )


def _convert_logarithmic(
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
    origin_ref_dim = simplify(origin_simpl.reference).dimension
    target_ref_dim = simplify(target_simpl.reference).dimension
    if origin_ref_dim != target_ref_dim:  # e.g. dBV -> dBm
        raise DimensionMismatchError(
            origin_simpl.reference,
            target_simpl.reference,
            origin_ref_dim,
            target_ref_dim,
        )

    ref_converter = convert(
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
        ln_b2_d = _fraction_to_decimal(_factor_to_fraction(b2, ctx=ctx)).ln(ctx)
        ln_ref_ratio_d = _fraction_to_decimal(
            _factor_to_fraction(ref_ratio, ctx=ctx)
        ).ln(ctx)
        return Converter(
            scale=k_ratio * Fraction(b1_d.ln(ctx)) / Fraction(ln_b2_d),
            offset=k2 * Fraction(ln_ref_ratio_d / ln_b2_d),
        )
    else:
        ln_b2_f = math.log(float(b2))
        return Converter(
            scale=float(k_ratio) * math.log(float(b1)) / ln_b2_f,
            offset=float(k2) * (math.log(float(ref_ratio)) / ln_b2_f),
        )


class _ConversionInfo(NamedTuple):
    expr: Expr
    """Absolute (non-translated, non-scaled) reference"""
    factor: Number | LazyProduct
    """Total scaling factor to convert from this unit to the absolute reference"""
    offset: Number | LazyProduct
    """Total offset to convert from this unit to the absolute reference"""


def _flatten(
    expr_simpl: SimplifiedExpr,
) -> _ConversionInfo:
    """Recursively flattens an expression into its absolute base unit."""
    if isinstance(
        expr_simpl,
        (BaseUnit, BaseDimension, Dimensionless, Logarithmic, Exp, Mul),
    ):
        # since `Exp(Scaled(x, a), b)` → `Scaled(Exp(x, b), a * b)`
        # similarly, `Mul((Scaled(...),))` → `Scaled(Mul((...),),)`
        return _ConversionInfo(expr_simpl, 1, 0)
    elif isinstance(expr_simpl, Scaled):
        # so `Scaled` should always be pushed to outmost level.
        # furthermore, since nested `Scaled(Scaled(x, c), d)` would simplify to
        # `Scaled(x, c * d)`, we don't need to recursively get the factor.
        factor = f.value if isinstance(f := expr_simpl.factor, Prefix) else f
        return _ConversionInfo(expr_simpl.reference, factor, 0)
    elif isinstance(expr_simpl, Tagged):
        info_ref = _flatten(expr_simpl.reference)  # type: ignore
        return _ConversionInfo(
            Tagged(info_ref.expr, expr_simpl.context),  # type: ignore
            info_ref.factor,
            info_ref.offset,
        )
    elif isinstance(expr_simpl, Translated):
        info_ref = _flatten(expr_simpl.reference)  # type: ignore
        assert info_ref.offset == 0, (
            f"inner reference of {expr_simpl=} should not have any offset"
        )
        # v_local = v_ref + offset_local
        #   v_abs = v_ref * factor_ref
        #         = v_local * factor_ref - offset_local * factor_ref
        new_offset = LazyProduct(
            (-1, expr_simpl.offset, *_products(info_ref.factor))
        )
        return _ConversionInfo(info_ref.expr, info_ref.factor, new_offset)
    else:  # pragma: no cover
        assert_never(expr_simpl)


#
# utilities
#


def _unwrap_tagged_or_aliased(expr: Expr) -> Expr:
    # `Translated` and `Logarithmic` are terminal, this plugs a loophole
    # NOTE: Alias(Alias(...)) and Tagged(Tagged(...)) is not allowed
    if isinstance(expr, (Tagged, Aliased)):
        return expr.reference
    return expr


def _products(
    factor: Number | LazyProduct | Prefix,
) -> Generator[tuple[Number, Exponent] | Number]:
    if isinstance(factor, Prefix):
        yield factor.value
    elif isinstance(factor, LazyProduct):
        for product in factor.products:
            yield product
    else:
        yield factor


def _products_inverse(
    factor: Number | LazyProduct | Prefix,
) -> Generator[tuple[Number, Exponent] | Number]:
    for item in _products(factor):
        if isinstance(item, tuple):
            base, exponent = item
            yield (base, -exponent)
        else:
            yield (item, -1)


def _factor_to_fraction(
    factor: Number | LazyProduct | Prefix, *, ctx: decimal.Context
) -> Fraction:
    if isinstance(factor, Prefix):
        return _factor_to_fraction(factor.value, ctx=ctx)
    if isinstance(factor, LazyProduct):
        return Fraction(factor.to_exact(ctx=ctx))
    elif isinstance(factor, (Decimal, float, int)):
        return Fraction(factor)
    elif isinstance(factor, SupportsDecimal):
        return Fraction(factor.to_decimal(ctx=ctx))
    elif not isinstance(factor, Fraction):
        raise assert_never(factor)
    return factor


def _fraction_to_decimal(fraction: Fraction) -> Decimal:
    return fraction.numerator / Decimal(fraction.denominator)


@dataclass(frozen=True)
class LazyProduct(SupportsFloat):
    r"""Represents a lazy product of a sequence of numbers raised to an optional
    exponent, i.e. $\prod_i x_i$, or $\prod_i x_i^{e_i}$.

    Lazy evaluation allows the choice between evaluating it to an exact value
    (taking longer to compute, useful for financial calculations) or an
    approximate float.
    """

    products: tuple[tuple[Number, Exponent] | Number, ...]

    @classmethod
    def from_derived_conversions(
        cls,
        derived_conversions: Sequence[tuple[Scaled, Exponent]],
    ) -> LazyProduct:
        products: list[tuple[Number, Exponent] | Number] = []
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
                if isinstance(base, SupportsDecimal):
                    base_decimal = base.to_decimal(ctx=ctx)
                elif isinstance(base, Decimal):
                    base_decimal = base
                elif isinstance(base, Fraction):  # *
                    base_decimal = _fraction_to_decimal(base)
                elif isinstance(base, float):
                    base_decimal = ctx.create_decimal_from_float(base)
                elif isinstance(base, int):  # ^
                    base_decimal = Decimal(base, context=ctx)
                else:  # pragma: no cover
                    assert_never(base)
                exponent_decimal = _fraction_to_decimal(exponent)
                product_decimal *= ctx.power(base_decimal, exponent_decimal)
            else:  # pragma: no cover
                assert_never(exponent)
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

    def __abs__(self) -> _E:
        return self


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

    def __abs__(self) -> _PI:
        return self


E: Final = _E()
PI: Final = _PI()


#
# errors
#


class IsqError(Exception):
    """Base exception for all errors raised by the isq library."""


@dataclass
class CompositionError(IsqError):
    outer: type[Expr]
    inner: Any
    msg: str
    help: str | None = None

    def __str__(self) -> str:  # pragma: no cover
        outer_name = (
            self.outer.name
            if isinstance(self.outer, Prefix)
            else self.outer.__name__
        )
        inner_repr = f"`{self.inner}` (of type `{type(self.inner).__name__}`)"

        message = (
            f"invalid composition: cannot apply `{outer_name}` to {inner_repr}."
            f"\nreason: {self.msg}"
        )
        if self.help:
            message += f"\nhelp: {self.help}"
        return message


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


# conversion
@dataclass
class KindMismatchError(IsqError):
    origin_kind: ExprKind
    target_kind: ExprKind

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
    dim_origin: Expr
    dim_target: Expr

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"cannot convert from `{self.origin}` to `{self.target}` due to "
            "incompatible dimensions."
            f"\ndimension of origin: `{self.dim_origin}`"
            f"\ndimension of target: `{self.dim_target}`"
        )


@dataclass
class UnitKindMismatchError(IsqError):
    kind: QtyKind
    unit: Expr
    dim_kind: Expr
    dim_unit: Expr

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"cannot create tagged unit for kind `{self.kind.context}` with "
            f"unit `{self.unit}`."
            f"\nexpected dimension of kind: `{self.dim_kind}`"
            f" (`{self.kind.unit_si}`)"
            f"\n   found dimension of unit: `{self.dim_unit}`"
            f" (`{self.unit}`)"
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
