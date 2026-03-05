from typing import Optional

from sqlglot import exp
from ..schemas import Issue
from ..dialects import register_rule
from .base import Rule


@register_rule()
class OrderByNoLimitRule(Rule):
    def check(self, sql: str, tree: exp.Expression, dialect: str) -> Optional[Issue]:
        has_order_by = tree.args.get("order") is not None
        has_limit = tree.args.get("limit") is not None
        
        if has_order_by and not has_limit:
            return Issue(
                code="ORDER_BY_NO_LIMIT",
                severity="info",
                message="ORDER BY without LIMIT may require sorting many rows; consider adding LIMIT if appropriate.",
            )
        return None
