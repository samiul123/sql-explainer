from typing import Optional

from sqlglot import exp
from ..schemas import Issue
from .base import Rule


class OuterJoinWhereFilterRule(Rule):
    def check(self, sql: str, tree: exp.Expression, dialect: str) -> Optional[Issue]:
        # Check for outer joins
        has_outer_join = False
        for j in tree.find_all(exp.Join):
            join_kind = (j.args.get("kind") or "").upper()
            if join_kind in ("LEFT", "RIGHT", "FULL", "LEFT OUTER", "RIGHT OUTER", "FULL OUTER"):
                has_outer_join = True
                break
        
        has_where = tree.args.get("where") is not None
        
        if has_outer_join and has_where:
            return Issue(
                code="OUTER_JOIN_WHERE_FILTER",
                severity="warning",
                message="Outer JOIN with WHERE clause may convert to INNER JOIN. Verify filters on outer-joined tables are in ON clause for correct semantics and better pushdown",
                evidence="Check if WHERE filters should be in JOIN ON conditions"
            )
        return None
