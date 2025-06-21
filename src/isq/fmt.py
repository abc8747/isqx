from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from .core import (
    Aliased,
    BaseDimension,
    BaseUnit,
    Dimensionless,
    Exp,
    Exponent,
    Expr,
    Factor,
    LazyFactor,
    Logarithmic,
    Mul,
    Scaled,
    Tagged,
    Translated,
    Visitor,
)


@runtime_checkable
class Formatter(Protocol):
    """Protocol for formatting an expression into a string."""

    def format(self, expr: Expr) -> str:
        """Format the given expression into a string."""
        ...


_SUPERSCRIPT_MAP = str.maketrans("0123456789-/", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻⸍")


@dataclass(frozen=True)
class BasicFormatter(Formatter, Visitor[str]):
    symbol_map: dict[str, str] = field(default_factory=dict)
    verbose: bool = True
    """If True, show definitions for all aliased units."""

    def format(self, expr: Expr) -> str:
        main_str = self.visit(expr)

        if not self.verbose:
            return main_str

        definitions: list[Definition] = []
        _collect_definitions(expr, 0, set(), definitions)
        if not definitions:
            return main_str
        return f"{main_str}, where:\n" + "\n".join(
            f"{'  ' * d.ident_level}- {d.node.name} = {self.visit(d.node.reference)}"
            for d in definitions
        )

    def visit_dimensionless(self, expr: Dimensionless) -> str:
        return self.symbol_map.get(expr.name, expr.name)

    def visit_base_dimension(self, expr: BaseDimension) -> str:
        return self.symbol_map.get(expr.name, expr.name)

    def visit_base_unit(self, expr: BaseUnit) -> str:
        return self.symbol_map.get(expr.name, expr.name)

    def visit_exp(self, expr: Exp) -> str:
        # TODO: a proper precedence system
        base_str = self.visit(expr.base)
        if isinstance(expr.base, (Mul, Scaled)):  # TODO: handle (expr**2)**3
            base_str = f"({base_str})"
        exponent_str = str(expr.exponent).translate(_SUPERSCRIPT_MAP)
        return f"{base_str}{exponent_str}"

    def visit_mul(self, expr: Mul) -> str:
        return " · ".join(self.visit(term) for term in expr.terms)

    def visit_scaled(self, expr: Scaled) -> str:
        ref_str = self.visit(expr.reference)
        if isinstance(expr.reference, Mul):
            ref_str = f"({ref_str})"
        if isinstance(expr.factor, LazyFactor):
            factor_str = " · ".join(
                self._format_product(factor) for factor in expr.factor.products
            )
        else:
            factor_str = str(expr.factor)
        return f"{factor_str} · {ref_str}"

    def _format_product(self, factor: Factor | tuple[Factor, Exponent]) -> str:
        if isinstance(factor, tuple):
            base, exponent = factor
            if exponent == 1:
                return str(base)
            return f"{base}{str(exponent).translate(_SUPERSCRIPT_MAP)}"
        return str(factor)

    def visit_aliased(self, expr: Aliased) -> str:
        return self.symbol_map.get(expr.name, expr.name)

    def visit_tagged(self, expr: Tagged) -> str:
        ref_str = self.visit(expr.reference)
        return f"{ref_str} {{ {expr.context!r} }}"  # TODO

    def visit_translated(self, expr: Translated) -> str:
        return self.symbol_map.get(expr.name, expr.name)

    def visit_logarithmic(self, expr: Logarithmic) -> str:
        return self.symbol_map.get(expr.name, expr.name)


@dataclass(frozen=True)
class Definition:
    ident_level: int
    node: Aliased | Translated | Logarithmic


def _collect_definitions(
    expression: Expr,
    indent_level: int,
    already_defined: set[str],
    definitions: list[Definition],
) -> None:
    direct_aliases: dict[str, Aliased | Translated | Logarithmic] = {}
    _collect_definable_nodes(expression, direct_aliases)

    for node in direct_aliases.values():
        if node.name in already_defined:
            continue
        already_defined.add(node.name)

        definitions.append(Definition(indent_level, node))
        _collect_definitions(
            node.reference,
            indent_level + 1,
            already_defined,
            definitions,
        )


def _collect_definable_nodes(
    expr: Expr,
    found: dict[str, Aliased | Translated | Logarithmic],
) -> None:
    if isinstance(expr, (Aliased, Translated, Logarithmic)):
        if expr.name not in found:
            found[expr.name] = expr
    elif isinstance(expr, Exp):
        _collect_definable_nodes(expr.base, found)
    elif isinstance(expr, (Scaled, Tagged, Translated, Logarithmic, Aliased)):
        _collect_definable_nodes(expr.reference, found)
    elif isinstance(expr, Mul):
        for term in expr.terms:
            _collect_definable_nodes(term, found)
