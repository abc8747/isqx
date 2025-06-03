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

import decimal
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from functools import lru_cache
from typing import (
    Any,
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


def _is_factor(value: Any) -> bool:
    return isinstance(value, (Decimal, Fraction, float, int))


@runtime_checkable
class Expr(Protocol):
    """Trait representing a tree-like unit or dimension expression."""

    @property
    def dimension(self) -> Expr: ...

    @property
    def kind(self) -> ExpressionKind: ...

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
        # TODO: add new parameter `keep_named: bool = False`
        # if `keep_named`, ft² will not be simplified to 0.09290304 m²
        ...  # pragma: no cover

    def to(self, target: Expr) -> Converter:
        """Return a converter object, that when called with a value, converts it
        to the target unit or dimension.

        :param target: The target unit or dimension to convert to. Must have
            compatible dimensions with the origin.
        """
        # NOTE: not using mixins because we want to track coverage
        # TODO: add new parameter `exact: bool = False` for money conversions
        # or should we just use the `.to(*, exact: bool = False)`?
        ...  # pragma: no cover


@dataclass(frozen=True)
class Dimensionless(Expr):
    name: str
    """Name for the dimensionless number, e.g. `reynolds`, `stanton`"""

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
        base_exponent_pairs: dict[Expr, Exponent] = {}
        derived_conversions: list[tuple[Scaled, Exponent]] = []
        _insert_root_expr(self, base_exponent_pairs, derived_conversions)
        return _get_simplified_expression(
            base_exponent_pairs,
            derived_conversions,
            name_hint=f"expr_{hash(self)}",
        )

    def to(self, target: Expr) -> Converter:
        return Converter.new(origin=self, target=target)


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
    def kind(self) -> ExpressionKind:
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
            name_hint=self.name or f"expr_{hash(self)}",
        )

    def to(self, target: Expr) -> Converter:
        return Converter.new(origin=self, target=target)


@dataclass(frozen=True)
class Scaled(Expr):
    reference: Expr
    """The unit or dimension that this unit or dimension is based on."""
    factor: Factor | LazyFactor
    """Multiplying this factor converts this value into the reference.
    For example, `1 ft = 0.3048 m`, so the factor is 0.3048.
    """
    name: str
    """Name of this unit or dimension."""

    @property
    def factor_approx(self) -> float | int:
        """Approximate factor to convert this unit or dimension to the
        reference unit or dimension."""
        factor = self.factor
        if isinstance(factor, LazyFactor):
            return factor.approx
        return float(_fraction_to_decimal(_factor_to_fraction(factor)))

    @property
    def kind(self) -> ExpressionKind:
        return self.reference.kind

    @property
    def dimension(self) -> Expr:
        return self.reference.dimension

    def simplify(self) -> Scaled:
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


#
# simplification
#
def _insert_root_expr(
    exp: Exp,
    base_exponent_pairs_mut: MutableMapping[Expr, Exponent],
    scaled_conversions_mut: MutableSequence[tuple[Scaled, Exponent]],
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
    base_exponent_pairs: Mapping[Expr, Exponent],
    scaled_conversions: list[tuple[Scaled, Exponent]],
    *,
    name_hint: str,
) -> Expr:
    no_conversions_involved = not scaled_conversions
    simplified_expr: Expr
    # remove zero exponents and ensure canonical order by names
    base_exponent_pairs_sorted = sorted(
        filter(lambda item: item[1] != 0, base_exponent_pairs.items()),
        key=lambda item: item[0].name,  # type: ignore
    )  # NOTE: `.name` is not required by `Expr` protocol!
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
                Exp(base, exponent)
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

    def __call__(self, value: Any, *, exact: bool = False) -> Any:
        """Convert a value in the origin unit to the target unit."""
        return value * (
            self.lazy_product.exact if exact else self.lazy_product.approx
        )


def _get_factor(expr_simpl: Expr) -> tuple[Expr, Factor | LazyFactor]:
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

    @property
    @lru_cache(maxsize=None)
    def exact(self) -> Fraction | Decimal:
        """Evaluate the lazy factor to an exact fraction or decimal.

        The return type depends on the products:

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
        ^ Sometimes, e.g. 4 ** (1/2)
        x No, decimal only
        ```

        For simplicity, only cases that can definitively be represented as a
        `Fraction` are returned as such. A `Decimal` is returned otherwise.
        """
        # NOTE: lru_cache doesn't invalidate with changes in Decimal context
        # TODO: figure out how to handle that
        ctx = decimal.getcontext()
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
                if exponent == 0:
                    continue
                return Fraction(0)
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

    @property
    @lru_cache(maxsize=None)
    def approx(self) -> float:
        product = 1.0
        for item in self.products:
            if isinstance(item, tuple):
                base, exponent = item
                if base == 0:
                    if exponent == 0:
                        continue
                    return 0.0
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
        return self.approx


@dataclass(frozen=True)
class Disambiguation:
    dimension: Expr  # e.g. meter

    def __call__(self, unit: Expr) -> Expr:
        # TODO: check dimension compatibility
        raise NotImplementedError
