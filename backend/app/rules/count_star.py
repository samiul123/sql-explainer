from typing import List

from sqlglot import exp
from ..schemas import Issue
from ..dialects import register_rule
from .base import Rule


@register_rule()
class CountStarRule(Rule):
    def check(self, sql: str, tree: exp.Expression, dialect: str) -> List[Issue]:
        for func in tree.find_all(exp.Count):
            for star in func.find_all(exp.Star):
                return [Issue(
                    code="COUNT_STAR",
                    severity="info",
                    message="COUNT(*) counts all rows including NULLs. If you need to count non-NULL values in a specific column, use COUNT(column_name) instead.",
                    evidence="COUNT(*)"
                )]
        return []
