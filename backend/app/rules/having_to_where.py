from typing import Optional

from sqlglot import exp
from ..schemas import Issue
from .base import Rule


class HavingToWhereRule(Rule):
    def check(self, sql: str, tree: exp.Expression, dialect: str) -> Optional[Issue]:
        has_having = tree.args.get("having") is not None
        has_group_by = tree.args.get("group") is not None
        
        if has_having and has_group_by:
            having_node = tree.args.get("having")
            if having_node:
                # Check if HAVING contains aggregate functions
                has_aggregate = bool(
                    having_node.find(exp.Count) or
                    having_node.find(exp.Sum) or
                    having_node.find(exp.Avg) or
                    having_node.find(exp.Max) or
                    having_node.find(exp.Min)
                )
                
                if not has_aggregate:
                    return Issue(
                        code="PUSHDOWN_HAVING_TO_WHERE",
                        severity="warning",
                        message="Non-aggregate filter in HAVING should be moved to WHERE to reduce rows before grouping (predicate pushdown)",
                        evidence=having_node.sql()[:100]
                    )
        return None
