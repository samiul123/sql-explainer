from typing import List

from sqlglot import exp
from ..schemas import Issue
from ..dialects import register_rule
from .base import Rule


@register_rule()
class DistinctUsedRule(Rule):
    def check(self, sql: str, tree: exp.Expression, dialect: str) -> List[Issue]:
        if tree.find(exp.Distinct):
            return [Issue(
                code="DISTINCT_USED",
                severity="info",
                message="DISTINCT can be expensive; if used to fix duplicates from joins, consider correcting join conditions instead.",
            )]
        return []
