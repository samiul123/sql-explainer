from typing import Optional

from sqlglot import exp
from ..schemas import Issue
from ..dialects import register_rule
from .base import Rule


@register_rule()
class SelectStarRule(Rule):
    def check(self, sql: str, tree: exp.Expression, dialect: str) -> Optional[Issue]:
        for star in tree.find_all(exp.Star):
            if isinstance(star.parent, exp.Select):
                return Issue(
                    code="SELECT_STAR",
                    severity="warning",
                    message="Avoid SELECT * in production queries; select only needed columns.",
                    evidence="SELECT *"
                )
        return None
