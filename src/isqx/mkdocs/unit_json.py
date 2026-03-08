"""Serialize units through a canonical public registry and a closed render AST.

Requirements:

- public ownership must be canonicalized before formatting; for example,
  `griffe` may encounter `isqx.aerospace.FT`, but the public ref must still
  resolve to `isqx.usc.FT`
- some public declarations must remain refable leaves, while others must
  inline; for example, `FT_PER_MIN` should serialize as `Mul(FT, Pow(MIN,-1))`
  rather than as a ref to `isqx.aerospace.FT_PER_MIN`

Three layers:

1. registry data structures plus registry construction
2. render-AST data structures plus lowering
3. JSON wire data structures plus encoding

The more direct "runtime object -> JSON" path was considered first, but left
too much hidden policy in ad hoc conditionals and made it hard to reason about.

Additional preferences:

- refs carry both `path` and `name`. The public path is for identity and
  linking, the explicit name is for display.
- named-leaf resolution is semantic, keyed by declaration kind and
  `Named.name`, rather than by runtime object identity.
- literal fallbacks remain part of the model on purpose. The AST is "closed"
  from the renderer's perspective, but it still needs explicit escape hatches
  for scalar or tag values we intentionally choose not to normalize further.
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import Literal, TypedDict, Union

if sys.version_info < (3, 10):
    from typing_extensions import TypeAlias, TypeGuard
else:
    from typing import TypeAlias, TypeGuard

from .. import (
    Aliased,
    BaseDimension,
    BaseUnit,
    Dimensionless,
    LazyProduct,
    Log,
    Mul,
    Scaled,
    Tagged,
    Translated,
)
from .. import Exp as UnitPower
from .. import Expr as IsqxExpr
from .._core import (
    DELTA,
    DIFFERENTIAL,
    INEXACT_DIFFERENTIAL,
    PI,
    E,
    Named,
    OriginAt,
    PhotometricCondition,
    Prefix,
    _Complex,
    _CoordinateSystem,
    _RatioBetween,
    _Tensor,
    assert_never,
)
from .._core import (
    Quantity as IsqxQuantity,
)

PublicDefinitions: TypeAlias = Mapping[str, str]
LeafDeclTag: TypeAlias = Literal[
    "dimensionless",
    "base_dimension",
    "base_unit",
    "alias",
    "translated",
]
RefPolicy: TypeAlias = Literal["leaf", "inline"]
NamedDeclKey: TypeAlias = tuple[LeafDeclTag, str]
NamedLeafExpr: TypeAlias = Union[
    Dimensionless,
    BaseDimension,
    BaseUnit,
    Aliased,
    Translated,
]
ScalarTag: TypeAlias = Literal[
    "constant",
    "fraction",
    "decimal",
    "int",
    "float",
    "literal",
]

#
# public registry
#


@dataclass(frozen=True)
class _UnitDeclBase:
    definition_path: str
    public_path: str
    ref_policy: RefPolicy


@dataclass(frozen=True)
class _NamedUnitDeclBase(_UnitDeclBase, Named):
    name: str


@dataclass(frozen=True)
class DimensionlessUnitDecl(_NamedUnitDeclBase):
    pass


@dataclass(frozen=True)
class BaseDimensionUnitDecl(_NamedUnitDeclBase):
    pass


@dataclass(frozen=True)
class BaseUnitUnitDecl(_NamedUnitDeclBase):
    pass


@dataclass(frozen=True)
class AliasUnitDecl(_NamedUnitDeclBase):
    expr: Aliased
    allow_prefix: bool


@dataclass(frozen=True)
class TranslatedUnitDecl(_NamedUnitDeclBase):
    expr: Translated


@dataclass(frozen=True)
class DerivedUnitDecl(_UnitDeclBase):
    expr: IsqxExpr


PublicLeafUnitDecl: TypeAlias = Union[
    DimensionlessUnitDecl,
    BaseDimensionUnitDecl,
    BaseUnitUnitDecl,
    AliasUnitDecl,
    TranslatedUnitDecl,
]
PublicUnitDecl: TypeAlias = Union[PublicLeafUnitDecl, DerivedUnitDecl]
NamedLeafDecl: TypeAlias = Union[NamedLeafExpr, PublicLeafUnitDecl]


@dataclass(frozen=True)
class UnitRegistry:
    by_public_path: Mapping[str, PublicUnitDecl]
    by_definition_path: Mapping[str, PublicUnitDecl]
    by_named_decl_key: Mapping[NamedDeclKey, PublicLeafUnitDecl]

    def get(self, identifier: str) -> PublicUnitDecl | None:
        return self.by_public_path.get(
            identifier
        ) or self.by_definition_path.get(identifier)

    def resolve_named_decl(
        self, expr: NamedLeafExpr
    ) -> PublicLeafUnitDecl | None:
        return self.by_named_decl_key.get(_named_decl_key(expr))


def build_unit_decl_table(
    definitions: Mapping[str, IsqxExpr],
    *,
    public_definitions: PublicDefinitions,
) -> UnitRegistry:
    """Build the canonical public unit registry."""

    by_public_path: dict[str, PublicUnitDecl] = {}
    by_definition_path: dict[str, PublicUnitDecl] = {}
    by_named_decl_key: dict[NamedDeclKey, PublicLeafUnitDecl] = {}
    source_paths: dict[str, str] = {}

    for definition_path, expr in definitions.items():
        public_path = public_definitions.get(definition_path)
        if public_path is None:
            continue

        existing_source = source_paths.get(public_path)
        if existing_source is not None and existing_source != definition_path:
            raise ValueError(
                "multiple unit definition paths resolved to the same public path: "
                f"{existing_source}, {definition_path} -> {public_path}"
            )

        decl = _build_public_unit_decl(
            definition_path=definition_path,
            public_path=public_path,
            expr=expr,
        )
        by_public_path[public_path] = decl
        by_definition_path[definition_path] = decl
        source_paths[public_path] = definition_path

        if isinstance(decl, _NamedUnitDeclBase):
            key = _named_decl_key(decl)
            existing_named = by_named_decl_key.get(key)
            if (
                existing_named is not None
                and existing_named.public_path != decl.public_path
            ):
                raise ValueError(
                    "multiple public declarations resolved to the same named key: "
                    f"{existing_named.public_path}, {decl.public_path} -> {key}"
                )
            by_named_decl_key[key] = decl

    return UnitRegistry(
        by_public_path=by_public_path,
        by_definition_path=by_definition_path,
        by_named_decl_key=by_named_decl_key,
    )


def _build_public_unit_decl(
    *,
    definition_path: str,
    public_path: str,
    expr: IsqxExpr,
) -> PublicUnitDecl:
    if isinstance(expr, Dimensionless):
        return DimensionlessUnitDecl(
            definition_path=definition_path,
            public_path=public_path,
            ref_policy="leaf",
            name=expr.name,
        )
    if isinstance(expr, BaseDimension):
        return BaseDimensionUnitDecl(
            definition_path=definition_path,
            public_path=public_path,
            ref_policy="leaf",
            name=expr.name,
        )
    if isinstance(expr, BaseUnit):
        return BaseUnitUnitDecl(
            definition_path=definition_path,
            public_path=public_path,
            ref_policy="leaf",
            name=expr.name,
        )
    if isinstance(expr, Aliased):
        return AliasUnitDecl(
            definition_path=definition_path,
            public_path=public_path,
            ref_policy="leaf",
            name=expr.name,
            expr=expr,
            allow_prefix=expr.allow_prefix,
        )
    if isinstance(expr, Translated):
        return TranslatedUnitDecl(
            definition_path=definition_path,
            public_path=public_path,
            ref_policy="leaf",
            name=expr.name,
            expr=expr,
        )
    return DerivedUnitDecl(
        definition_path=definition_path,
        public_path=public_path,
        ref_policy="inline",
        expr=expr,
    )


def _named_decl_key(value: NamedLeafDecl) -> NamedDeclKey:
    return (_named_decl_tag(value), value.name)


def _named_decl_tag(value: NamedLeafDecl) -> LeafDeclTag:
    if isinstance(value, (Dimensionless, DimensionlessUnitDecl)):
        return "dimensionless"
    if isinstance(value, (BaseDimension, BaseDimensionUnitDecl)):
        return "base_dimension"
    if isinstance(value, (BaseUnit, BaseUnitUnitDecl)):
        return "base_unit"
    if isinstance(value, (Aliased, AliasUnitDecl)):
        return "alias"
    if isinstance(value, (Translated, TranslatedUnitDecl)):
        return "translated"
    raise assert_never(value)


#
# render ast
#


@dataclass(frozen=True)
class _LowerContext:
    unit_registry: UnitRegistry
    expanding_paths: frozenset[str] = frozenset()


@dataclass(frozen=True)
class ConstantScalarAst:
    text: str
    value: Literal["E", "PI"]


@dataclass(frozen=True)
class FractionScalarAst:
    text: str
    numerator: int
    denominator: int


@dataclass(frozen=True)
class DecimalScalarAst:
    text: str
    value: str


@dataclass(frozen=True)
class IntScalarAst:
    text: str
    value: int


@dataclass(frozen=True)
class FloatScalarAst:
    text: str
    value: float


@dataclass(frozen=True)
class LiteralScalarAst:
    text: str
    value: str


UnitScalarAst: TypeAlias = Union[
    ConstantScalarAst,
    FractionScalarAst,
    DecimalScalarAst,
    IntScalarAst,
    FloatScalarAst,
    LiteralScalarAst,
]


@dataclass(frozen=True)
class LazyProductItemAst:
    base: UnitScalarAst
    exponent: UnitScalarAst | None = None


@dataclass(frozen=True)
class NumberFactorAst:
    value: UnitScalarAst


@dataclass(frozen=True)
class PrefixFactorAst:
    name: str
    value: UnitScalarAst


@dataclass(frozen=True)
class LazyProductFactorAst:
    products: tuple[LazyProductItemAst, ...]


UnitFactorAst: TypeAlias = Union[
    NumberFactorAst,
    PrefixFactorAst,
    LazyProductFactorAst,
]


@dataclass(frozen=True)
class RefExprAst(Named):
    path: str
    name: str


@dataclass(frozen=True)
class PowExprAst:
    base: UnitExprAst
    exponent: UnitScalarAst


@dataclass(frozen=True)
class MulExprAst:
    terms: tuple[UnitExprAst, ...]


@dataclass(frozen=True)
class ScaledExprAst:
    factor: UnitFactorAst
    unit: UnitExprAst


@dataclass(frozen=True)
class UnitQuantityAst:
    value: UnitFactorAst
    unit: UnitExprAst


@dataclass(frozen=True)
class RatioBetweenTagAst:
    numerator: UnitExprAst
    denominator_expr: UnitExprAst | None = None
    denominator_quantity: UnitQuantityAst | None = None


@dataclass(frozen=True)
class OriginAtTagAst:
    quantity: UnitQuantityAst | None = None
    value: str | None = None


@dataclass(frozen=True)
class LiteralTagAst:
    tag: str
    text: str
    value: str | None = None
    rank: int | None = None


UnitTagAst: TypeAlias = Union[
    RatioBetweenTagAst,
    OriginAtTagAst,
    LiteralTagAst,
]


@dataclass(frozen=True)
class TaggedExprAst:
    unit: UnitExprAst
    tags: tuple[UnitTagAst, ...]


@dataclass(frozen=True)
class LogExprAst:
    base: UnitScalarAst
    unit: UnitExprAst


UnitExprAst: TypeAlias = Union[
    RefExprAst,
    PowExprAst,
    MulExprAst,
    ScaledExprAst,
    TaggedExprAst,
    LogExprAst,
]


@dataclass(frozen=True)
class _NamedDeclAstBase(Named):
    path: str
    name: str


@dataclass(frozen=True)
class DimensionlessDeclAst(_NamedDeclAstBase):
    pass


@dataclass(frozen=True)
class BaseDimensionDeclAst(_NamedDeclAstBase):
    pass


@dataclass(frozen=True)
class BaseUnitDeclAst(_NamedDeclAstBase):
    pass


@dataclass(frozen=True)
class AliasDeclAst(_NamedDeclAstBase):
    expr: UnitExprAst
    allow_prefix: bool


@dataclass(frozen=True)
class TranslatedDeclAst(_NamedDeclAstBase):
    expr: UnitExprAst
    offset: UnitScalarAst


@dataclass(frozen=True)
class DerivedDeclAst:
    path: str
    expr: UnitExprAst


UnitDeclAst: TypeAlias = Union[
    DimensionlessDeclAst,
    BaseDimensionDeclAst,
    BaseUnitDeclAst,
    AliasDeclAst,
    TranslatedDeclAst,
    DerivedDeclAst,
]


def _lower_unit_decl_ast(
    decl: PublicUnitDecl,
    *,
    unit_decls: UnitRegistry,
) -> UnitDeclAst:
    ctx = _LowerContext(
        unit_registry=unit_decls,
        expanding_paths=frozenset({decl.public_path}),
    )

    if isinstance(decl, DimensionlessUnitDecl):
        return DimensionlessDeclAst(path=decl.public_path, name=decl.name)
    if isinstance(decl, BaseDimensionUnitDecl):
        return BaseDimensionDeclAst(path=decl.public_path, name=decl.name)
    if isinstance(decl, BaseUnitUnitDecl):
        return BaseUnitDeclAst(path=decl.public_path, name=decl.name)
    if isinstance(decl, AliasUnitDecl):
        return AliasDeclAst(
            path=decl.public_path,
            name=decl.name,
            expr=_lower_unit_expr_ast(decl.expr.reference, ctx),
            allow_prefix=decl.allow_prefix,
        )
    if isinstance(decl, TranslatedUnitDecl):
        return TranslatedDeclAst(
            path=decl.public_path,
            name=decl.name,
            expr=_lower_unit_expr_ast(decl.expr.reference, ctx),
            offset=_lower_scalar_ast(decl.expr.offset),
        )
    if isinstance(decl, DerivedUnitDecl):
        return DerivedDeclAst(
            path=decl.public_path,
            expr=_lower_unit_expr_ast(decl.expr, ctx),
        )
    raise assert_never(decl)


def _lower_unit_expr_ast(expr: IsqxExpr, ctx: _LowerContext) -> UnitExprAst:
    ref = _lower_ref_ast(expr, ctx)
    if ref is not None:
        return ref
    if isinstance(expr, UnitPower):
        return PowExprAst(
            base=_lower_unit_expr_ast(expr.base, ctx),
            exponent=_lower_scalar_ast(expr.exponent),
        )
    if isinstance(expr, Mul):
        return MulExprAst(
            terms=tuple(_lower_unit_expr_ast(term, ctx) for term in expr.terms)
        )
    if isinstance(expr, Scaled):
        return ScaledExprAst(
            factor=_lower_factor_ast(expr.factor),
            unit=_lower_unit_expr_ast(expr.reference, ctx),
        )
    if isinstance(expr, Tagged):
        return TaggedExprAst(
            unit=_lower_unit_expr_ast(expr.reference, ctx),
            tags=tuple(_lower_tag_ast(tag, ctx) for tag in expr.tags),
        )
    if isinstance(expr, Log):
        return LogExprAst(
            base=_lower_scalar_ast(expr.base),
            unit=_lower_unit_expr_ast(expr.reference, ctx),
        )
    if _is_named_decl(expr):
        raise ValueError(
            "named leaf did not resolve to a public declaration: "
            f"{_display_name(expr)}"
        )
    raise TypeError(f"unsupported unit expression {type(expr).__name__}")


def _lower_ref_ast(
    expr: IsqxExpr,
    ctx: _LowerContext,
) -> RefExprAst | None:
    if not _is_named_decl(expr):
        return None

    public_decl = ctx.unit_registry.resolve_named_decl(expr)
    if public_decl is None:
        raise ValueError(
            "named leaf resolved outside the public declaration table: "
            f"{_display_name(expr)}"
        )
    if public_decl.public_path in ctx.expanding_paths:
        return None
    if public_decl.ref_policy == "inline":
        return None
    return RefExprAst(path=public_decl.public_path, name=expr.name)


def _is_named_decl(expr: IsqxExpr) -> TypeGuard[NamedLeafExpr]:
    return isinstance(
        expr,
        (Dimensionless, BaseDimension, BaseUnit, Aliased, Translated),
    )


def _display_name(expr: object) -> str:
    if isinstance(expr, Named):
        return expr.name
    return type(expr).__name__.lower()


def _lower_scalar_ast(value: object) -> UnitScalarAst:
    if value is E:
        return ConstantScalarAst(text=str(value), value="E")
    if value is PI:
        return ConstantScalarAst(text=str(value), value="PI")
    if isinstance(value, Fraction):
        return FractionScalarAst(
            text=str(value),
            numerator=value.numerator,
            denominator=value.denominator,
        )
    if isinstance(value, Decimal):
        return DecimalScalarAst(text=str(value), value=str(value))
    if isinstance(value, int) and not isinstance(value, bool):
        return IntScalarAst(text=str(value), value=value)
    if isinstance(value, float):
        return FloatScalarAst(text=repr(value), value=value)
    return LiteralScalarAst(text=str(value), value=str(value))


def _lower_factor_ast(factor: LazyProduct | Prefix | object) -> UnitFactorAst:
    if isinstance(factor, Prefix):
        return PrefixFactorAst(
            name=factor.name,
            value=_lower_scalar_ast(factor.value),
        )
    if isinstance(factor, LazyProduct):
        products: list[LazyProductItemAst] = []
        for item in factor.products:
            if isinstance(item, tuple):
                products.append(
                    LazyProductItemAst(
                        base=_lower_scalar_ast(item[0]),
                        exponent=_lower_scalar_ast(item[1]),
                    )
                )
            else:
                products.append(
                    LazyProductItemAst(base=_lower_scalar_ast(item))
                )
        return LazyProductFactorAst(products=tuple(products))
    return NumberFactorAst(value=_lower_scalar_ast(factor))


def _lower_quantity_ast(
    quantity: IsqxQuantity,
    ctx: _LowerContext,
) -> UnitQuantityAst:
    return UnitQuantityAst(
        value=_lower_factor_ast(quantity.value),
        unit=_lower_unit_expr_ast(quantity.unit, ctx),
    )


def _lower_tag_ast(tag: object, ctx: _LowerContext) -> UnitTagAst:
    if isinstance(tag, _RatioBetween):
        if isinstance(tag.denominator, IsqxQuantity):
            return RatioBetweenTagAst(
                numerator=_lower_unit_expr_ast(tag.numerator, ctx),
                denominator_quantity=_lower_quantity_ast(tag.denominator, ctx),
            )
        return RatioBetweenTagAst(
            numerator=_lower_unit_expr_ast(tag.numerator, ctx),
            denominator_expr=_lower_unit_expr_ast(tag.denominator, ctx),
        )
    if isinstance(tag, OriginAt):
        if isinstance(tag.location, IsqxQuantity):
            return OriginAtTagAst(
                quantity=_lower_quantity_ast(tag.location, ctx)
            )
        return OriginAtTagAst(value=repr(tag.location))
    if tag is DELTA:
        return LiteralTagAst(tag="delta", text="Δ")
    if tag is DIFFERENTIAL:
        return LiteralTagAst(tag="differential", text="differential")
    if tag is INEXACT_DIFFERENTIAL:
        return LiteralTagAst(
            tag="inexact_differential",
            text="inexact differential",
        )
    if isinstance(tag, _Tensor):
        return LiteralTagAst(tag="tensor", text=repr(tag), rank=tag.rank)
    if isinstance(tag, _CoordinateSystem):
        return LiteralTagAst(
            tag="coordinate_system",
            text=repr(tag),
            value=tag.name,
        )
    if isinstance(tag, _Complex):
        return LiteralTagAst(tag="complex", text=repr(tag))
    if isinstance(tag, PhotometricCondition):
        return LiteralTagAst(
            tag="photometric_condition",
            text=repr(tag),
            value=tag.kind,
        )
    return LiteralTagAst(tag="literal", text=repr(tag))


#
# json wire format
#


class ScalarJsonData(TypedDict, total=False):
    text: str
    value: int | float | str
    numerator: int
    denominator: int


class UnitScalarJsonNode(TypedDict):
    tag: ScalarTag
    data: ScalarJsonData


class LazyProductItemJson(TypedDict, total=False):
    base: UnitScalarJsonNode
    exponent: UnitScalarJsonNode


class NumberFactorJsonData(TypedDict):
    value: UnitScalarJsonNode


class NumberFactorJsonNode(TypedDict):
    tag: Literal["number"]
    data: NumberFactorJsonData


class PrefixFactorJsonData(TypedDict):
    name: str
    value: UnitScalarJsonNode


class PrefixFactorJsonNode(TypedDict):
    tag: Literal["prefix"]
    data: PrefixFactorJsonData


class LazyProductFactorJsonData(TypedDict):
    products: list[LazyProductItemJson]


class LazyProductFactorJsonNode(TypedDict):
    tag: Literal["lazy_product"]
    data: LazyProductFactorJsonData


UnitFactorJson: TypeAlias = Union[
    NumberFactorJsonNode,
    PrefixFactorJsonNode,
    LazyProductFactorJsonNode,
]


class PublicRefJsonData(TypedDict):
    path: str
    name: str


class RefExprJsonNode(TypedDict):
    tag: Literal["ref"]
    data: PublicRefJsonData


class PowExprJsonData(TypedDict):
    base: UnitExprJson
    exponent: UnitScalarJsonNode


class PowExprJsonNode(TypedDict):
    tag: Literal["pow"]
    data: PowExprJsonData


class MulExprJsonData(TypedDict):
    terms: list[UnitExprJson]


class MulExprJsonNode(TypedDict):
    tag: Literal["mul"]
    data: MulExprJsonData


class ScaledExprJsonData(TypedDict):
    factor: UnitFactorJson
    unit: UnitExprJson


class ScaledExprJsonNode(TypedDict):
    tag: Literal["scaled"]
    data: ScaledExprJsonData


class UnitQuantityJsonNode(TypedDict):
    value: UnitFactorJson
    unit: UnitExprJson


class RatioBetweenTagJsonData(TypedDict, total=False):
    numerator: UnitExprJson
    denominatorExpr: UnitExprJson
    denominatorQuantity: UnitQuantityJsonNode


class RatioBetweenTagJsonNode(TypedDict):
    tag: Literal["ratio_between"]
    data: RatioBetweenTagJsonData


class OriginAtTagJsonData(TypedDict, total=False):
    quantity: UnitQuantityJsonNode
    value: str


class OriginAtTagJsonNode(TypedDict):
    tag: Literal["origin_at"]
    data: OriginAtTagJsonData


class LiteralTagJsonData(TypedDict, total=False):
    text: str
    value: str
    rank: int


class LiteralTagJsonNode(TypedDict):
    tag: str
    data: LiteralTagJsonData


UnitTagJson: TypeAlias = Union[
    RatioBetweenTagJsonNode,
    OriginAtTagJsonNode,
    LiteralTagJsonNode,
]


class TaggedExprJsonData(TypedDict):
    unit: UnitExprJson
    tags: list[UnitTagJson]


class TaggedExprJsonNode(TypedDict):
    tag: Literal["tagged"]
    data: TaggedExprJsonData


class LogExprJsonData(TypedDict):
    base: UnitScalarJsonNode
    unit: UnitExprJson


class LogExprJsonNode(TypedDict):
    tag: Literal["log"]
    data: LogExprJsonData


UnitExprJson: TypeAlias = Union[
    RefExprJsonNode,
    PowExprJsonNode,
    MulExprJsonNode,
    ScaledExprJsonNode,
    TaggedExprJsonNode,
    LogExprJsonNode,
]


class NamedDeclJsonData(TypedDict):
    path: str
    name: str


class DimensionlessDeclJsonNode(TypedDict):
    tag: Literal["dimensionless"]
    data: NamedDeclJsonData


class BaseDimensionDeclJsonNode(TypedDict):
    tag: Literal["base_dimension"]
    data: NamedDeclJsonData


class BaseUnitDeclJsonNode(TypedDict):
    tag: Literal["base_unit"]
    data: NamedDeclJsonData


class AliasDeclJsonData(TypedDict):
    path: str
    name: str
    expr: UnitExprJson
    allowPrefix: bool


class AliasDeclJsonNode(TypedDict):
    tag: Literal["alias"]
    data: AliasDeclJsonData


class TranslatedDeclJsonData(TypedDict):
    path: str
    name: str
    expr: UnitExprJson
    offset: UnitScalarJsonNode


class TranslatedDeclJsonNode(TypedDict):
    tag: Literal["translated"]
    data: TranslatedDeclJsonData


class DerivedDeclJsonData(TypedDict):
    path: str
    expr: UnitExprJson


class DerivedDeclJsonNode(TypedDict):
    tag: Literal["derived"]
    data: DerivedDeclJsonData


UnitDeclJson: TypeAlias = Union[
    DimensionlessDeclJsonNode,
    BaseDimensionDeclJsonNode,
    BaseUnitDeclJsonNode,
    AliasDeclJsonNode,
    TranslatedDeclJsonNode,
    DerivedDeclJsonNode,
]


def serialize_unit_expr(
    expr: IsqxExpr,
    *,
    unit_decls: UnitRegistry,
    expanding_paths: frozenset[str] = frozenset(),
) -> UnitExprJson:
    """Lower a runtime expression directly to the JSON wire format."""

    return _encode_unit_expr(
        _lower_unit_expr_ast(
            expr,
            _LowerContext(
                unit_registry=unit_decls,
                expanding_paths=expanding_paths,
            ),
        )
    )


def serialize_unit_decl(
    identifier: str,
    *,
    unit_decls: UnitRegistry,
) -> UnitDeclJson | None:
    """Serialize one declaration from the public unit registry."""

    decl = unit_decls.get(identifier)
    if decl is None:
        return None
    return _encode_unit_decl(_lower_unit_decl_ast(decl, unit_decls=unit_decls))


def serialize_unit_decls(
    *, unit_decls: UnitRegistry
) -> dict[str, UnitDeclJson]:
    """Serialize the full public unit registry."""

    return {
        public_path: _encode_unit_decl(
            _lower_unit_decl_ast(decl, unit_decls=unit_decls)
        )
        for public_path, decl in unit_decls.by_public_path.items()
    }


def _encode_scalar(scalar: UnitScalarAst) -> UnitScalarJsonNode:
    if isinstance(scalar, ConstantScalarAst):
        return UnitScalarJsonNode(
            tag="constant",
            data=ScalarJsonData(text=scalar.text, value=scalar.value),
        )
    if isinstance(scalar, FractionScalarAst):
        return UnitScalarJsonNode(
            tag="fraction",
            data=ScalarJsonData(
                text=scalar.text,
                numerator=scalar.numerator,
                denominator=scalar.denominator,
            ),
        )
    if isinstance(scalar, DecimalScalarAst):
        return UnitScalarJsonNode(
            tag="decimal",
            data=ScalarJsonData(text=scalar.text, value=scalar.value),
        )
    if isinstance(scalar, IntScalarAst):
        return UnitScalarJsonNode(
            tag="int",
            data=ScalarJsonData(text=scalar.text, value=scalar.value),
        )
    if isinstance(scalar, FloatScalarAst):
        return UnitScalarJsonNode(
            tag="float",
            data=ScalarJsonData(text=scalar.text, value=scalar.value),
        )
    if isinstance(scalar, LiteralScalarAst):
        return UnitScalarJsonNode(
            tag="literal",
            data=ScalarJsonData(text=scalar.text, value=scalar.value),
        )
    raise assert_never(scalar)


def _encode_factor(factor: UnitFactorAst) -> UnitFactorJson:
    if isinstance(factor, NumberFactorAst):
        return NumberFactorJsonNode(
            tag="number",
            data=NumberFactorJsonData(value=_encode_scalar(factor.value)),
        )
    if isinstance(factor, PrefixFactorAst):
        return PrefixFactorJsonNode(
            tag="prefix",
            data=PrefixFactorJsonData(
                name=factor.name,
                value=_encode_scalar(factor.value),
            ),
        )
    if isinstance(factor, LazyProductFactorAst):
        products: list[LazyProductItemJson] = []
        for product in factor.products:
            item = LazyProductItemJson(base=_encode_scalar(product.base))
            if product.exponent is not None:
                item["exponent"] = _encode_scalar(product.exponent)
            products.append(item)
        return LazyProductFactorJsonNode(
            tag="lazy_product",
            data=LazyProductFactorJsonData(products=products),
        )
    raise assert_never(factor)


def _encode_quantity(quantity: UnitQuantityAst) -> UnitQuantityJsonNode:
    return UnitQuantityJsonNode(
        value=_encode_factor(quantity.value),
        unit=_encode_unit_expr(quantity.unit),
    )


def _encode_tag(tag: UnitTagAst) -> UnitTagJson:
    if isinstance(tag, RatioBetweenTagAst):
        ratio_data = RatioBetweenTagJsonData(
            numerator=_encode_unit_expr(tag.numerator)
        )
        if tag.denominator_expr is not None:
            ratio_data["denominatorExpr"] = _encode_unit_expr(
                tag.denominator_expr
            )
        if tag.denominator_quantity is not None:
            ratio_data["denominatorQuantity"] = _encode_quantity(
                tag.denominator_quantity
            )
        return RatioBetweenTagJsonNode(tag="ratio_between", data=ratio_data)
    if isinstance(tag, OriginAtTagAst):
        origin_data = OriginAtTagJsonData()
        if tag.quantity is not None:
            origin_data["quantity"] = _encode_quantity(tag.quantity)
        if tag.value is not None:
            origin_data["value"] = tag.value
        return OriginAtTagJsonNode(tag="origin_at", data=origin_data)
    if isinstance(tag, LiteralTagAst):
        literal_data = LiteralTagJsonData(text=tag.text)
        if tag.value is not None:
            literal_data["value"] = tag.value
        if tag.rank is not None:
            literal_data["rank"] = tag.rank
        return LiteralTagJsonNode(tag=tag.tag, data=literal_data)
    raise assert_never(tag)


def _encode_unit_expr(expr: UnitExprAst) -> UnitExprJson:
    if isinstance(expr, RefExprAst):
        return RefExprJsonNode(
            tag="ref",
            data=PublicRefJsonData(path=expr.path, name=expr.name),
        )
    if isinstance(expr, PowExprAst):
        return PowExprJsonNode(
            tag="pow",
            data=PowExprJsonData(
                base=_encode_unit_expr(expr.base),
                exponent=_encode_scalar(expr.exponent),
            ),
        )
    if isinstance(expr, MulExprAst):
        return MulExprJsonNode(
            tag="mul",
            data=MulExprJsonData(
                terms=[_encode_unit_expr(term) for term in expr.terms]
            ),
        )
    if isinstance(expr, ScaledExprAst):
        return ScaledExprJsonNode(
            tag="scaled",
            data=ScaledExprJsonData(
                factor=_encode_factor(expr.factor),
                unit=_encode_unit_expr(expr.unit),
            ),
        )
    if isinstance(expr, TaggedExprAst):
        return TaggedExprJsonNode(
            tag="tagged",
            data=TaggedExprJsonData(
                unit=_encode_unit_expr(expr.unit),
                tags=[_encode_tag(tag) for tag in expr.tags],
            ),
        )
    if isinstance(expr, LogExprAst):
        return LogExprJsonNode(
            tag="log",
            data=LogExprJsonData(
                base=_encode_scalar(expr.base),
                unit=_encode_unit_expr(expr.unit),
            ),
        )
    raise assert_never(expr)


def _encode_unit_decl(decl: UnitDeclAst) -> UnitDeclJson:
    if isinstance(decl, DimensionlessDeclAst):
        return DimensionlessDeclJsonNode(
            tag="dimensionless",
            data=NamedDeclJsonData(path=decl.path, name=decl.name),
        )
    if isinstance(decl, BaseDimensionDeclAst):
        return BaseDimensionDeclJsonNode(
            tag="base_dimension",
            data=NamedDeclJsonData(path=decl.path, name=decl.name),
        )
    if isinstance(decl, BaseUnitDeclAst):
        return BaseUnitDeclJsonNode(
            tag="base_unit",
            data=NamedDeclJsonData(path=decl.path, name=decl.name),
        )
    if isinstance(decl, AliasDeclAst):
        return AliasDeclJsonNode(
            tag="alias",
            data=AliasDeclJsonData(
                path=decl.path,
                name=decl.name,
                expr=_encode_unit_expr(decl.expr),
                allowPrefix=decl.allow_prefix,
            ),
        )
    if isinstance(decl, TranslatedDeclAst):
        return TranslatedDeclJsonNode(
            tag="translated",
            data=TranslatedDeclJsonData(
                path=decl.path,
                name=decl.name,
                expr=_encode_unit_expr(decl.expr),
                offset=_encode_scalar(decl.offset),
            ),
        )
    if isinstance(decl, DerivedDeclAst):
        return DerivedDeclJsonNode(
            tag="derived",
            data=DerivedDeclJsonData(
                path=decl.path,
                expr=_encode_unit_expr(decl.expr),
            ),
        )
    raise assert_never(decl)
