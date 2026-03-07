from typing import List

from sqlglot import exp
from ..schemas import Issue
from ..dialects import register_rule
from .base import Rule


@register_rule()
class SubqueryPushdownRule(Rule):
    def check(self, sql: str, tree: exp.Expression, dialect: str) -> List[Issue]:
        has_subquery = bool(tree.find(exp.Subquery))
        has_where = tree.args.get("where") is not None
        
        if has_subquery and has_where:
            return [Issue(
                code="SUBQUERY_PUSHDOWN_OPPORTUNITY",
                severity="info",
                message="Consider pushing applicable WHERE filters into subqueries to reduce materialized row count",
                evidence="Review if filters can be applied inside derived tables"
            )]
        return []
