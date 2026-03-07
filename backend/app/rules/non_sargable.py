"""Detect non-sargable query patterns that prevent index usage"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from sqlglot import exp

from ..schemas import Issue
from ..dialects import register_rule
from .base import Rule


@dataclass
class Finding:
    kind: str
    sql: str
    reason: str


COMPARISON_NODES = (
    exp.EQ,
    exp.NEQ,
    exp.GT,
    exp.GTE,
    exp.LT,
    exp.LTE,
    exp.Between,
    exp.In,
    exp.Like,
    exp.ILike,
)


def has_column(node: exp.Expression | None) -> bool:
    """Check if node or any descendant contains a Column"""
    return node is not None and any(isinstance(x, exp.Column) for x in node.walk())


def get_column_names(node: exp.Expression | None) -> str:
    """Extract column name(s) from a node"""
    if node is None:
        return "column"
    cols = [col.sql() for col in node.find_all(exp.Column)]
    if not cols:
        return "column"
    return ", ".join(cols)


def get_expression_type(node: exp.Expression | None) -> str:
    """Get the type of expression wrapping the column"""
    if node is None:
        return "expression"
    if isinstance(node, exp.Func):
        return f"{node.key.upper()}()"
    if isinstance(node, (exp.Add, exp.Sub, exp.Mul, exp.Div, exp.Mod)):
        return "arithmetic"
    if isinstance(node, (exp.Cast, exp.TryCast)):
        return "CAST()"
    if isinstance(node, exp.Case):
        return "CASE"
    if isinstance(node, exp.Neg):
        return "negation"
    return "expression"


def is_expression_on_column(node: exp.Expression | None) -> bool:
    """Check if node is a function/expression wrapping a column"""
    if node is None:
        return False

    # Plain column is okay (sargable)
    if isinstance(node, exp.Column):
        return False

    # Function on a column is non-sargable
    if isinstance(node, exp.Func) and has_column(node):
        return True

    # Arithmetic / unary / cast / case expressions containing a column
    suspicious = (
        exp.Add,
        exp.Sub,
        exp.Mul,
        exp.Div,
        exp.Mod,
        exp.Neg,
        exp.Paren,
        exp.Cast,
        exp.TryCast,
        exp.Case,
    )
    return isinstance(node, suspicious) and has_column(node)


def is_leading_wildcard_like(node: exp.Expression) -> bool:
    """Check if LIKE/ILIKE pattern starts with %"""
    if not isinstance(node, (exp.Like, exp.ILike)):
        return False

    pattern = node.expression
    if isinstance(pattern, exp.Literal) and pattern.is_string:
        value = pattern.this
        return isinstance(value, str) and value.startswith("%")
    return False


def inspect_predicate(predicate: exp.Expression) -> List[Finding]:
    """Inspect a predicate (WHERE or ON clause) for non-sargable patterns"""
    findings: List[Finding] = []

    for node in predicate.walk():
        if not isinstance(node, COMPARISON_NODES):
            continue

        left = getattr(node, "this", None)
        right = getattr(node, "expression", None)

        # 1) Function/expression on left side with column inside
        if is_expression_on_column(left):
            col = get_column_names(left)
            expr_type = get_expression_type(left)
            findings.append(
                Finding(
                    kind="expression_on_column",
                    sql=node.sql(),
                    reason=f"Column '{col}' wrapped in {expr_type} prevents index usage",
                )
            )

        # 2) Function/expression on right side with column inside
        if is_expression_on_column(right):
            col = get_column_names(right)
            expr_type = get_expression_type(right)
            findings.append(
                Finding(
                    kind="expression_on_column",
                    sql=node.sql(),
                    reason=f"Column '{col}' wrapped in {expr_type} prevents index usage",
                )
            )

        # 3) LIKE '%x' - leading wildcard
        if is_leading_wildcard_like(node):
            col = get_column_names(left)
            findings.append(
                Finding(
                    kind="leading_wildcard_like",
                    sql=node.sql(),
                    reason=f"LIKE on column '{col}' starts with %, prevents index seeks",
                )
            )

        # 4) BETWEEN with expression on column
        if isinstance(node, exp.Between):
            target = node.this
            if is_expression_on_column(target):
                col = get_column_names(target)
                expr_type = get_expression_type(target)
                findings.append(
                    Finding(
                        kind="expression_on_column",
                        sql=node.sql(),
                        reason=f"BETWEEN on column '{col}' uses {expr_type}, prevents index usage",
                    )
                )

    return findings


@register_rule()
class NonSargableRule(Rule):
    """Detect non-sargable patterns that prevent index usage"""

    def check(self, sql: str, tree: exp.Expression, dialect: str) -> List[Issue]:
        findings: List[Finding] = []

        # Check WHERE clause
        where = tree.args.get("where")
        if where:
            findings.extend(inspect_predicate(where.this))

        # Check JOIN ON clauses
        for join in tree.find_all(exp.Join):
            on_expr = join.args.get("on")
            if on_expr:
                findings.extend(inspect_predicate(on_expr))

        # Convert all findings to Issues
        return [
            Issue(
                code="NON_SARGABLE",
                severity="warning",
                message=f"{f.reason}. This prevents index usage.",
                evidence=f.sql,
            )
            for f in findings
        ]
