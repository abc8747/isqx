from __future__ import annotations

import decimal
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import (
    Any,
    Hashable,
    Literal,
    Mapping,
    MutableMapping,
    MutableSequence,
    NamedTuple,
    Protocol,
    Sequence,
    Union,
    runtime_checkable,
)

from typing_extensions import TypeAlias

ExpressionKind: TypeAlias = Literal["dimensionless", "unit", "dimension"]
Factor: TypeAlias = Union[Decimal, Fraction, float, int]


@runtime_checkable
class Expr(Protocol):
    """A protocol that a "unit-like" expression must implement.

    It may be of the following forms:

    | Type                                      | Example                   |
    | ----------------------------------------- | ------------------------- |
    | [dimensionless number][isq.Dimensionless] | `Reynolds`, `Prandtl`     |
    | [base dimension][isq.BaseDimension]       | [length][isq.DIM_LENGTH]  |
    | [base unit][isq.BaseUnit]                 | [meter][isq.M]            |
    | [expression raised to a power][isq.Exp]   | `Exp(METER, 2)`           |
    | [product of expressions][isq.Mul]         | `Mul(NEWTON, METER)`      |
    | [scaled expression][isq.Scaled]           | [feet][isq.FT] = 0.3048 m |
    | [disambiguated][isq.Disambiguated]        | true vs ground speed      |
    | [translated expression][isq.Translated]^  | [celsius][isq.CELSIUS]    |

    ^ translated units are *terminal*, meaning it cannot be further
      [exponentiated][isq.Exp], [multiplied][isq.Mul], [scaled][isq.Scaled] or
      [translated][isq.Translated] to form a more complex expression. However,
      it can be further [disambiguated][isq.Disambiguated] (e.g. surface
      temperature vs ISA temperature).
    """

    @property
    def dimension(self) -> Expr:
        r"""Return the dimension of this "unit-like" expression.
        Note that it does not perform simplification.

        Examples:

        - `Exp(M, 2)` -> `Exp(DIM_LENGTH, 2)`
        - `Mul(M, Exp(S, -1))` -> `Mul(DIM_LENGTH, Exp(DIM_TIME, -1))`
        """
        ...

    @property
    def kind(self) -> ExpressionKind:
        r"""Whether this expression is a unit, dimension, or dimensionless."""
        ...

    def simplify(self) -> Expr:
        """Flatten a complex tree-like structure into a simple canonical form,
        including: distributing exponents, combining like terms and merging
        nested scaling factors.

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
        return Converter.new(origin=self, target=target, exact=exact, ctx=ctx)


@dataclass(frozen=True)
class Dimensionless(ConvertMixin, Expr):
    name: str
    """Name for the dimensionless number, e.g. `reynolds`, `prandtl`"""

    @property
    def dimension(self) -> Dimensionless:
        return self

    @property
    def kind(self) -> ExpressionKind:
        return "dimensionless"

    def simplify(self) -> Expr:
        return self


@dataclass(frozen=True)
class BaseDimension(ConvertMixin, Expr):
    name: str
    """Name for the base dimension, e.g. `L`, `M`, `T`"""

    @property
    def dimension(self) -> BaseDimension:
        return self

    @property
    def kind(self) -> ExpressionKind:
        return "dimension"

    def simplify(self) -> Expr:
        return self


@dataclass(frozen=True)
class BaseUnit(ConvertMixin, Expr):
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

    def simplify(self) -> Expr:
        return self


Exponent: TypeAlias = Union[int, Fraction]
"""An exponent, generally small integers, which can be positive, negative,
or a fraction, but not zero"""


@dataclass(frozen=True)
class Exp(ConvertMixin, Expr):
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
        if isinstance(ref := _unwrap_disambiguated(self.base), Translated):
            raise ValueError(
                f"translated expression `{ref.name}` is terminal: it cannot be"
                f"futher raised to the power of {self.exponent}"
                f"\nhelp: did you mean to exponentiate {ref.reference}?"
            )  # prevent ℃². J ℃⁻¹ should be written as J K⁻¹

    @property
    def kind(self) -> ExpressionKind:
        return self.base.kind

    @property
    def dimension(self) -> Exp:
        return Exp(self.base.dimension, self.exponent)

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
        return _build_canonical_expr(
            base_exponent_pairs,
            derived_conversions,
            name_hint=f"expr_{hash(self)}",
        )


@dataclass(frozen=True)
class Mul(ConvertMixin, Expr):
    """Products of powers of an expression."""

    terms: tuple[Expr, ...]
    """A tuple of expressions to be multiplied, preserving the order."""
    name: str | None = None
    """Name for this expression, e.g. `newton`, `joule`"""

    def __post_init__(self) -> None:
        n_terms = len(self.terms)
        if n_terms == 0:
            raise ValueError("terms must not be empty, use `Dimensionless`")
        kinds = []
        for term in self.terms:
            if isinstance(ref := _unwrap_disambiguated(term), Translated):
                raise ValueError(
                    f"translated expression `{ref}` is terminal:"
                    "it cannot be multiplied with other expressions"
                    "\nhelp: use its absolute reference instead"
                    f": `{ref.reference}`"
                )  # prevent ℃ * ℃
            kinds.append(term.kind)
        unique_kinds = set(kinds) - {"dimensionless"}
        if len(unique_kinds) != 1:
            raise ValueError("terms must all be either `unit` or `dimension`")

    @property
    def dimension(self) -> Mul:
        return Mul(
            tuple(term.dimension for term in self.terms),
            name=self.name,
        )

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
        return _build_canonical_expr(
            base_exponent_pairs,
            derived_conversions,
            name_hint=self.name or f"expr_{hash(self)}",
        )


@dataclass(frozen=True)
class Scaled(ConvertMixin, Expr):
    reference: Expr
    """The unit or dimension that this unit or dimension is based on."""
    factor: Factor | LazyFactor
    """The exact factor to multiply to this unit to convert it to the reference.
    For example, `1 ft = 0.3048 m`, so the factor is 0.3048.
    """
    name: str
    """Name of this unit or dimension, e.g. `feet`."""
    allow_prefix: bool = False
    """Whether to allow prefixes to be attached. This should only be true for
    some units like `liter`, `tonne`, `electronvolt`"""

    def __post_init__(self) -> None:
        if isinstance(ref := _unwrap_disambiguated(self.reference), Translated):
            raise ValueError(
                f"translated expression `{ref.name}` is terminal:"
                f"it cannot be further scaled"
            )  # prevent 13 * ℃

    @property
    def kind(self) -> ExpressionKind:
        return self.reference.kind

    @property
    def dimension(self) -> Expr:
        return self.reference.dimension

    def simplify(self) -> Scaled:
        """Merges nested scaling factors into a single [`LazyFactor`][isq.LazyFactor].

        For example, `Scaled(Scaled(M, 2), Fraction(1, 3))` will be simplified
        to `Scaled(M, LazyFactor((Fraction(1, 3), 2))))`. Note that we do not
        eagerly evaluate the multiplication.
        """
        products: list[tuple[Factor, Exponent] | Factor] = []
        expr: Expr = self
        while True:
            if not isinstance(expr, Scaled):
                expr = expr.simplify()
                break
            if isinstance(expr.factor, LazyFactor):  # by previous simplify()
                products.extend(expr.factor.products)
            else:
                products.append(expr.factor)
            expr = expr.reference
        return Scaled(expr, LazyFactor(tuple(products)), self.name)


@dataclass(frozen=True)
class Prefix:
    """A factory, which when multiplied by a [base unit][isq.BaseUnit] or
    [**named** derived unit][isq.Mul], returs a [scaled unit][isq.Scaled].

    Note that this is not an [isq.Expr][], but a *constructor helper*.
    """

    factor: Factor
    name: str
    """Name of this prefix, e.g. `milli`, `kibi`"""

    def __mul__(self, rhs: BaseUnit | Mul | Scaled) -> Scaled:
        if rhs.kind != "unit":
            raise TypeError(
                f"cannot apply prefix `{self.name}` to {rhs=}"
                f"\nhelp: expected rhs to be a unit, but rhs is `{rhs.kind}`"
            )
        if isinstance(rhs, BaseUnit) and rhs.name == "kilogram":
            raise TypeError(
                f"cannot apply prefix `{self.name}` to `KG`."
                "\nhelp: apply it to `GRAM` instead."
            )  # kilo(kilogram)
        if isinstance(rhs, Mul) and rhs.name is None:
            raise TypeError(
                f"cannot apply prefix `{self.name}` to unnamed derived unit"
                f" {rhs}\nhelp: must be a named derived unit like Newtons."
            )  # kilo(m s⁻¹)
        if isinstance(rhs, Scaled):
            if not rhs.allow_prefix:
                raise TypeError(
                    f"cannot apply another prefix `{self.name}` to a unit that"
                    "does not allow further prefixes"
                )  # kilo(kilowatt)
            if self.name == "kilo" and rhs.name == "gram":
                raise TypeError(
                    "cannot apply prefix KILO to GRAM"
                    "\nhelp: use isq.KG directly instead"
                )
        if isinstance(_unwrap_disambiguated(rhs), Translated):
            raise TypeError(
                f"cannot apply prefix `{self.name}` to translated unit {rhs=}"
            )  # kilo(℃)
        if not isinstance(rhs, (BaseUnit, Mul, Scaled)):
            raise TypeError(
                f"cannot apply prefix `{self.name}` to {rhs=} ({type(rhs)=})"
                f"\nhelp: rhs must be `GRAM`, or a `BaseUnit` (e.g. meters, "
                "except kg) or a named derived unit (e.g. newtons)."
            )  # kilo(m³), kilo(Re)

        new_name = f"{self.name}{rhs.name}"
        return Scaled(rhs, self.factor, name=new_name, allow_prefix=False)

    # NOTE: not defining __rmul__ to avoid confusion


@dataclass(frozen=True)
class Disambiguated(ConvertMixin, Expr):
    """An expression decorated with a semantic context tag.

    This is used to disambiguate between quantities that share the same
    physical dimension but have different meanings, e.g.,
    geopotential altitude vs. geometric altitude.
    """

    reference: Expr
    """The expression that this disambiguation wraps, e.g. `METER`"""
    context: Hashable
    """A hashable identifier, e.g. `geopotential`, a tuple of contexts"""

    def __post_init__(self) -> None:
        if isinstance(self.reference, Disambiguated):
            raise ValueError(
                "nesting disambiguated expressions is not allowed,"
                "consider using a tuple to store multiple contexts instead"
            )

    @property
    def kind(self) -> ExpressionKind:
        return self.reference.kind

    @property
    def dimension(self) -> Disambiguated:
        return Disambiguated(self.reference.dimension, self.context)

    def simplify(self) -> Disambiguated:
        simplified_ref = self.reference.simplify()
        return Disambiguated(simplified_ref, self.context)


@dataclass(frozen=True)
class Translated(ConvertMixin, Expr):
    """An expression offsetted from some reference unit."""

    reference: Expr
    """The expression that this expression is based on (e.g., `K` for `DEGC`)"""
    offset: Factor
    """The exact offset to add to the reference to get this unit.
    For example, `℃ = K - 273.15`, so the offset is -273.15."""
    name: str

    def __post_init__(self) -> None:
        if isinstance(self.reference, Translated):
            raise TypeError("nesting translated units is not allowed")
        if not isinstance(
            ref := _unwrap_disambiguated(self.reference), (BaseUnit, Scaled)
        ):
            raise TypeError(
                f"reference of translated unit `{self.name}` must be a"
                f"BaseUnit or Scaled, not `{type(ref).__name__}`"
            )

    @property
    def kind(self) -> ExpressionKind:
        return self.reference.kind

    @property
    def dimension(self) -> Expr:
        return self.reference.dimension

    def simplify(self) -> Translated:
        return Translated(self.reference.simplify(), self.offset, self.name)


def _unwrap_disambiguated(expr: Expr) -> Expr:
    if isinstance(expr, Disambiguated):
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
    if isinstance(
        expr, (Dimensionless, BaseDimension, BaseUnit, Disambiguated)
    ):
        # we hit a fundamental-like unit (we treat disambiguated obj as unique
        # bases). add its accumulated exponent
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
        raise ValueError(f"unknown {type(expr)=}")


def _build_canonical_expr(
    base_exponent_pairs: Mapping[Expr, Exponent],
    scaled_conversions: list[tuple[Scaled, Exponent]],
    *,
    name_hint: str,
) -> Expr:
    r"""Construct a canonical expression from flattened parts.

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
        simplified_expr = Dimensionless(
            name=f"dimensionless_form_of_{name_hint}"
        )
    elif len(base_exponent_pairs_sorted) == 1:
        base, exponent = base_exponent_pairs_sorted[0]
        simplified_expr = base if exponent == 1 else Exp(base, exponent)
    else:
        simplified_expr = Mul(
            tuple(
                base if exponent == 1 else Exp(base, exponent)
                for base, exponent in base_exponent_pairs_sorted
            ),
            name=name_hint if no_conversions_involved else None,
        )
    if no_conversions_involved:
        return simplified_expr

    return Scaled(
        reference=simplified_expr,
        factor=LazyFactor.from_derived_conversions(scaled_conversions),
        name=name_hint,
    )


#
# unit/dimension conversions
#


@dataclass(frozen=True)
class Converter:
    scale: Factor
    offset: Factor
    origin_simpl: Expr  # for dbg
    target_simpl: Expr

    @classmethod
    def new(
        cls,
        origin: Expr,
        target: Expr,
        *,
        exact: bool,
        ctx: decimal.Context | None = None,
    ) -> Converter:
        """Create a new unit converter from one unit to another.

        Checks that the underlying dimension are compatible
        (e.g. `USD/year` and `HKD/hour`) and computes the total scaling factor.
        """
        origin_simpl = origin.simplify()
        target_simpl = target.simplify()
        if origin_simpl.kind != target_simpl.kind:
            raise ValueError(
                "expected self and target to have the same kind, "
                f"but {origin_simpl.kind} != {target_simpl.kind}"
            )

        info_origin = _flatten(origin_simpl)
        info_target = _flatten(target_simpl)
        origin_dim = info_origin.expr.dimension
        target_dim = info_target.expr.dimension
        origin_dim_terms = (
            origin_dim.terms if isinstance(origin_dim, Mul) else (origin_dim,)
        )
        target_dim_terms = (
            target_dim.terms if isinstance(target_dim, Mul) else (target_dim,)
        )
        if origin_dim_terms != target_dim_terms:
            # NOTE: we can probably have a better error message here
            # show the diff between two trees
            raise ValueError(
                f"expected origin and target to have the same dimension, "
                f"but {origin_dim_terms} != {target_dim_terms}"
            )
        # we have:
        #   v_abs = scale_origin * v_origin + offset_origin
        #   v_abs = scale_target * v_target + offset_target
        # then:
        #   v_target = (scale_origin / scale_target) * v_origin +
        #              (offset_origin - offset_target) / scale_target
        scale_origin: list[tuple[Factor, Exponent] | Factor] = []
        if isinstance(info_origin.factor, LazyFactor):
            scale_origin.extend(info_origin.factor.products)
        else:
            scale_origin.append(info_origin.factor)
        inv_scale_target: list[tuple[Factor, Exponent] | Factor] = []
        if isinstance(info_target.factor, LazyFactor):
            for item in info_target.factor.products:
                if isinstance(item, tuple):
                    base, exponent = item
                    inv_scale_target.append((base, -exponent))
                else:
                    inv_scale_target.append((item, -1))
        else:
            inv_scale_target.append((info_target.factor, -1))
        scale = LazyFactor(tuple([*scale_origin, *inv_scale_target]))

        offset_numerator = _factor_to_fraction(
            info_origin.offset, ctx=ctx
        ) - _factor_to_fraction(info_target.offset, ctx=ctx)
        offset = LazyFactor(tuple([offset_numerator, *inv_scale_target]))

        return cls(
            scale=scale.to_exact(ctx=ctx) if exact else scale.to_approx(),
            offset=offset.to_exact(ctx=ctx) if exact else offset.to_approx(),
            origin_simpl=origin_simpl,
            target_simpl=target_simpl,
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
    # NOTE: by design Exp, Mul and Scaled cannot contain Translated so offset=0
    if isinstance(expr_simpl, (BaseUnit, BaseDimension, Dimensionless)):
        return ConversionInfo(expr_simpl, 1, 0)
    elif isinstance(expr_simpl, Exp):
        # if expr is `Exp(Scaled(x, a), b)`, simplifying will result in
        # `Scaled(Exp(x, b), a * b)` so it'll be handled by the `Scaled` case
        return ConversionInfo(expr_simpl, 1, 0)
    elif isinstance(expr_simpl, Mul):
        # similarly, `Mul((Scaled(...),))` → `Scaled(Mul((...),),)`
        return ConversionInfo(expr_simpl, 1, 0)
    elif isinstance(expr_simpl, Scaled):
        # so `Scaled` should always be pushed to outmost level.
        # furthermore, since nested `Scaled(Scaled(x, c), d)` would simplify to
        # `Scaled(x, c * d)`, we don't need to recursively get the factor.
        return ConversionInfo(expr_simpl.reference, expr_simpl.factor, 0)
    elif isinstance(expr_simpl, Disambiguated):
        info_ref = _flatten(expr_simpl.reference)
        return ConversionInfo(
            Disambiguated(info_ref.expr, expr_simpl.context),
            info_ref.factor,
            info_ref.offset,
        )
    elif isinstance(expr_simpl, Translated):
        info_ref = _flatten(expr_simpl.reference)
        assert info_ref.offset == 0, (
            f"inner reference of {expr_simpl=} should not have any offset"
        )
        factor_ref = (
            info_ref.factor.products
            if isinstance(info_ref.factor, LazyFactor)
            else (info_ref.factor,)
        )
        # v_local = v_ref + offset_local
        #   v_abs = v_ref * factor_ref =
        #         = v_local * factor_ref - offset_local * factor_ref
        new_offset = LazyFactor((-1, expr_simpl.offset, *factor_ref))
        return ConversionInfo(info_ref.expr, info_ref.factor, new_offset)
    else:  # pragma: no cover
        raise ValueError(f"unknown expression {expr_simpl}")


def _factor_to_fraction(
    factor: Factor | LazyFactor, *, ctx: decimal.Context | None = None
) -> Fraction:
    if isinstance(factor, LazyFactor):
        return Fraction(factor.to_exact(ctx=ctx))
    elif isinstance(factor, (Decimal, float, int)):
        return Fraction(factor)
    elif not isinstance(factor, Fraction):
        raise ValueError(f"unknown {type(factor)=}")  # pragma: no cover
    return factor


def _fraction_to_decimal(fraction: Fraction) -> Decimal:
    return fraction.numerator / Decimal(fraction.denominator)


@dataclass(frozen=True)
class LazyFactor:
    r"""Represents a scaling factor as a sequence of products.

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
            if isinstance(scaled.factor, LazyFactor):  # by previous simplify()
                for inner_item in scaled.factor.products:
                    if isinstance(inner_item, tuple):
                        base, inner_exp = inner_item
                        products.append((base, inner_exp * exponent))
                    else:
                        products.append((inner_item, exponent))
            else:
                products.append((scaled.factor, exponent))
        return cls(tuple(products))

    def to_approx(self) -> float:
        """Reduce it to an approximate float value. Good enough for most
        applications."""
        product = 1.0
        for item in self.products:
            if isinstance(item, tuple):
                base, exponent = item
                exp_value = float(exponent)
                if base == 0:
                    if exp_value > 0:
                        return 0.0
                    if exp_value == 0:
                        continue  # 0 ** 0 = 1
                if base == 1:
                    continue
                product *= float(base) ** float(exponent)
            else:
                if item == 0:
                    return 0.0
                if item == 1:
                    continue
                product *= float(item)
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
                product_fraction *= _factor_to_fraction(item)
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
                    base_fraction = _factor_to_fraction(base)
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
                    raise ValueError(f"unknown {type(base)=}")
                exponent_decimal = _fraction_to_decimal(exponent)
                product_decimal *= ctx.power(base_decimal, exponent_decimal)
            else:  # pragma: no cover
                raise ValueError(f"unknown {type(exponent)=}")
        if product_decimal == Decimal(1):
            return product_fraction
        return _fraction_to_decimal(product_fraction) * product_decimal


# NOTE: for a registry, one option is to adopt https://peps.python.org/pep-0487/#subclass-registration:
# - have a `Registrable` mixin with `__init_subclass__` so the act of defining a class `S` automatically adds it to a global dict
# - this guarantees completeness with zero boilerplate
# - BUT... importing a module containing units would have side effects. explicit registration is prob a better idea
# - we need to be careful of circular imports (avoid importing ft before m)
