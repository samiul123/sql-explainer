from typing import Optional

from sqlglot import exp
from ..schemas import Issue
from .base import Rule


class FunctionBlocksPushdownRule(Rule):
    def check(self, sql: str, tree: exp.Expression, dialect: str) -> Optional[Issue]:
        where = tree.args.get("where")
        if not where:
            return None
        
        # Look for non-sargable functions in WHERE
        nonsargable_funcs = {
            "DATE": "Rewrite as: column >= 'date' AND column < 'date+1'",
            "YEAR": "Rewrite as: column >= 'year-01-01' AND column < 'year+1-01-01'",
            "MONTH": "Use date range instead",
            "LOWER": "Use case-insensitive collation or functional index",
            "UPPER": "Use case-insensitive collation or functional index",
            "TRIM": "Store data trimmed or use functional index",
        }
        
        for func in where.find_all(exp.Func):
            func_name = func.key.upper() if hasattr(func, 'key') else ""
            if func_name in nonsargable_funcs:
                # Check if function wraps a column
                if func.find(exp.Column):
                    return Issue(
                        code="FUNCTION_BLOCKS_PUSHDOWN",
                        severity="warning",
                        message=f"Function {func_name}(column) prevents index usage and early filtering. {nonsargable_funcs[func_name]}",
                        evidence=func.sql()
                    )
        return None
