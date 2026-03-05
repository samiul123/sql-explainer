from typing import Optional

from sqlglot import exp
from ..schemas import Issue
from .base import Rule


class OrInWhereRule(Rule):
    def check(self, sql: str, tree: exp.Expression, dialect: str) -> Optional[Issue]:
        where = tree.args.get("where")
        if where:
            for _ in where.find_all(exp.Or):
                return Issue(
                    code="OR_IN_WHERE",
                    severity="info",
                    message="OR conditions can reduce index effectiveness; consider UNION ALL or refactoring if performance is an issue.",
                )
        return None
