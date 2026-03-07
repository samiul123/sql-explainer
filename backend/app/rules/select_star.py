from typing import List

from sqlglot import exp
from ..schemas import Issue
from ..dialects import register_rule
from .base import Rule


@register_rule()
class SelectStarRule(Rule):
    def check(self, sql: str, tree: exp.Expression, dialect: str) -> List[Issue]:
        select_node = tree.find(exp.Select)
        if select_node and select_node.find(exp.Star):
            return [Issue(
                code="SELECT_STAR",
                severity="warning",
                message="Avoid SELECT * in production queries; select only needed columns.",
                evidence="SELECT *"
            )]
        return []
