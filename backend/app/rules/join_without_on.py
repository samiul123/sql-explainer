from typing import List

from sqlglot import exp
from ..schemas import Issue
from ..dialects import register_rule
from .base import Rule


@register_rule()
class JoinWithoutOnRule(Rule):
    def check(self, sql: str, tree: exp.Expression, dialect: str) -> List[Issue]:
        for j in tree.find_all(exp.Join):
            on_clause = j.args.get("on")
            join_kind = (j.args.get("kind") or "JOIN").upper()
            
            if on_clause is None and join_kind not in ("CROSS", "CROSS JOIN"):
                return [Issue(
                    code="JOIN_WITHOUT_ON",
                    severity="critical",
                    message="JOIN without ON can create a cartesian product (huge result set).",
                    evidence=f"JOIN {j.this.sql() if j.this else ''}"
                )]
        return []
