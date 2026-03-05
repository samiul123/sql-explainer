from typing import Optional

from sqlglot import exp
from ..schemas import Issue
from .base import Rule


class DistinctUsedRule(Rule):
    def check(self, sql: str, tree: exp.Expression, dialect: str) -> Optional[Issue]:
        if tree.find(exp.Distinct):
            return Issue(
                code="DISTINCT_USED",
                severity="info",
                message="DISTINCT can be expensive; if used to fix duplicates from joins, consider correcting join conditions instead.",
            )
        return None
