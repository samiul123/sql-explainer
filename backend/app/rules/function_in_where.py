from typing import Optional

from sqlglot import exp
from ..schemas import Issue
from .base import Rule


class FunctionInWhereRule(Rule):
    def check(self, sql: str, tree: exp.Expression, dialect: str) -> Optional[Issue]:
        where = tree.args.get("where")
        if where:
            functions_found = []
            for func in where.find_all(exp.Func):
                functions_found.append(func.sql())
            
            if functions_found:
                return Issue(
                    code="FUNCTION_IN_WHERE",
                    severity="warning",
                    message="Functions in WHERE can prevent index usage (e.g., DATE(col), LOWER(col)). Consider rewriting predicates.",
                    evidence="; ".join(functions_found[:3])
                )
        return None
