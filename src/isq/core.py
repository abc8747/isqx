from __future__ import annotations

import decimal
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from functools import lru_cache
from typing import (
    Any,
    Hashable,
    Literal,
    Mapping,
    MutableMapping,
    MutableSequence,
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
        # TODO: add new parameter `keep_named: bool = False`
        # why: we sometimes dont want ft² to be simplified to 0.09290304 m²
        ...

    def to(self, target: Expr) -> Converter:
        """Return a converter object, that when called with a value, converts it
        to the target unit or dimension.

        :param target: The target unit or dimension to convert to. Must have
            compatible dimensions with the origin.
        """
        # TODO: add new parameter `exact: bool = False` for money conversions
        # or should we just use the `.to(*, exact: bool = False)`?
        ...


@dataclass(frozen=True)
class Dimensionless(Expr):
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

    def to(self, target: Expr) -> Converter:
        return Converter.new(origin=self, target=target)


@dataclass(frozen=True)
class BaseDimension(Expr):
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

    def to(self, target: Expr) -> Converter:
        return Converter.new(origin=self, target=target)


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
    def kind(self) -> ExpressionKind:
        return "unit"

    def simplify(self) -> Expr:
        return self

    def to(self, target: Expr) -> Converter:
        return Converter.new(origin=self, target=target)


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

    def to(self, target: Expr) -> Converter:
        return Converter.new(origin=self, target=target)


@dataclass(frozen=True)
class Mul(Expr):
    """Products of powers of an expression."""

    terms: tuple[Expr, ...]
    """A tuple of expressions to be multiplied, preserving the order."""
    name: str | None = None
    """Name for this expression, e.g. `newton`, `joule`"""

    def __post_init__(self) -> None:
        n_terms = len(self.terms)
        if n_terms == 0:
            raise ValueError("terms must not be empty, use `Dimensionless`")
        unique_kinds = set(t.kind for t in self.terms) - {"dimensionless"}
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

    def to(self, target: Expr) -> Converter:
        return Converter.new(origin=self, target=target)


@dataclass(frozen=True)
class Scaled(Expr):
    reference: Expr
    """The unit or dimension that this unit or dimension is based on."""
    factor: Factor | LazyFactor
    """The exact factor to convert this unit or dimension to the reference.
    For example, `1 ft = 0.3048 m`, so the factor is 0.3048.
    """
    name: str
    """Name of this unit or dimension, e.g. `feet`."""

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

    def to(self, target: Expr) -> Converter:
        return Converter.new(origin=self, target=target)


@dataclass(frozen=True)
class Disambiguated(Expr):
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
    def dimension(self) -> Expr:
        return Disambiguated(self.reference.dimension, self.context)

    def simplify(self) -> Expr:
        simplified_ref = self.reference.simplify()
        return Disambiguated(simplified_ref, self.context)

    def to(self, target: Expr) -> Converter:
        return Converter.new(origin=self, target=target)


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
    origin_simpl: Expr
    target_simpl: Expr
    lazy_product: LazyFactor

    @classmethod
    def new(cls, origin: Expr, target: Expr) -> Converter:
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

        origin_inner_simpl, origin_factor = _separate_factor(origin_simpl)
        target_inner_simpl, target_factor = _separate_factor(target_simpl)
        origin_dim = origin_inner_simpl.dimension
        target_dim = target_inner_simpl.dimension
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
        products: list[tuple[Factor, Exponent] | Factor] = []
        if isinstance(origin_factor, LazyFactor):
            products.extend(origin_factor.products)
        else:
            products.append(origin_factor)
        if isinstance(target_factor, LazyFactor):
            for item in target_factor.products:
                if isinstance(item, tuple):
                    base, exponent = item
                    products.append((base, -exponent))
                else:
                    products.append((item, -1))
        else:
            products.append((target_factor, -1))
        return cls(
            origin_simpl=origin_simpl,
            target_simpl=target_simpl,
            lazy_product=LazyFactor(tuple(products)),
        )

    def __call__(
        self,
        value: Any,
        *,
        exact: bool = False,
        ctx: decimal.Context | None = None,
    ) -> Any:
        """Convert a value in the origin unit to the target unit."""
        return value * (
            self.lazy_product.to_exact(ctx=ctx)
            if exact
            else self.lazy_product.to_approx()
        )


def _separate_factor(expr_simpl: Expr) -> tuple[Expr, Factor | LazyFactor]:
    """Unpack a simplified expression into its unit and scaling factor.

    This is used in [Converter.new][] to isolate the core unit from its
    numerical scale. Examples:

    - `Scaled(M, 0.3048)` → `(M, 0.3048)`
    - `M` → `(M, 1.0)`
    """

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
    elif isinstance(expr_simpl, Disambiguated):
        inner_ref, factor = _separate_factor(expr_simpl.reference)
        return Disambiguated(inner_ref, expr_simpl.context), factor
    else:  # pragma: no cover
        raise ValueError(f"unknown expression {expr_simpl}")


def _factor_to_fraction(factor: Factor) -> Fraction:
    if isinstance(factor, (Decimal, float, int)):
        factor = Fraction(factor)
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

    @lru_cache(maxsize=None)
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

    # NOTE: not using lru_cache because decimal.Context is not hashable
    # it is the caller's responsibility to cache it
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
