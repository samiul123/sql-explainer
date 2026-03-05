from typing import Optional
import re

from sqlglot import exp
from ..schemas import Issue
from ..dialects import register_rule
from .base import Rule


@register_rule()
class LeadingWildcardLikeRule(Rule):
    def check(self, sql: str, tree: exp.Expression, dialect: str) -> Optional[Issue]:
        if re.search(r"like\s+'%[^']*'", sql.lower()):
            return Issue(
                code="LEADING_WILDCARD_LIKE",
                severity="warning",
                message="Leading wildcard LIKE (e.g., LIKE '%foo') usually prevents index usage.",
            )
        return None
