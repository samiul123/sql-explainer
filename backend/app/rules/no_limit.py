from typing import List

from sqlglot import exp
from ..schemas import Issue
from ..dialects import register_rule
from .base import Rule


@register_rule()
class NoLimitRule(Rule):
    def check(self, sql: str, tree: exp.Expression, dialect: str) -> List[Issue]:
        has_limit = tree.args.get("limit") is not None
        s = sql.lower()
        if not has_limit and "select" in s and "count(" not in s:
            return [Issue(
                code="NO_LIMIT",
                severity="info",
                message="Query has no LIMIT. For exploration or large tables, consider adding LIMIT.",
            )]
        return []
