from __future__ import annotations

from typing import List, Tuple, Optional
import re

import sqlglot
from sqlglot import exp

from ..schemas import Issue
from ..rules import (
    Rule,
    SelectStarRule,
    CountStarRule,
    NoLimitRule,
    LeadingWildcardLikeRule,
    OrInWhereRule,
    FunctionInWhereRule,
    JoinWithoutOnRule,
    DistinctUsedRule,
    OrderByNoLimitRule,
    HavingToWhereRule,
    FunctionBlocksPushdownRule,
    OuterJoinWhereFilterRule,
    SubqueryPushdownRule,
)

DIALECT_MAP = {
    "postgres": "postgres",
    "mysql": "mysql",
    "sqlite": "sqlite",
    "tsql": "tsql",
    "bigquery": "bigquery",
    "snowflake": "snowflake",
}


def normalize_sql(sql: str) -> str:
    """Basic SQL cleanup"""
    sql = sql.strip()
    sql = re.sub(r"[ \t]+", " ", sql)
    return sql


class DialectLinter:
    """Base linter that manages rules for a specific dialect"""
    
    def __init__(self, dialect: str):
        self.dialect = dialect
        self.rules: List[Rule] = []
        self._register_rules()
    
    def _register_rules(self):
        """Override in subclasses to register dialect-specific rules"""
        # Register common rules that apply to all dialects
        self.add_rule(SelectStarRule())
        self.add_rule(CountStarRule())
        self.add_rule(NoLimitRule())
        self.add_rule(LeadingWildcardLikeRule())
        self.add_rule(OrInWhereRule())
        self.add_rule(FunctionInWhereRule())
        self.add_rule(JoinWithoutOnRule())
        self.add_rule(DistinctUsedRule())
        self.add_rule(OrderByNoLimitRule())
        self.add_rule(HavingToWhereRule())
        self.add_rule(FunctionBlocksPushdownRule())
        self.add_rule(OuterJoinWhereFilterRule())
        self.add_rule(SubqueryPushdownRule())
    
    def add_rule(self, rule: Rule):
        """Add a rule to this linter"""
        self.rules.append(rule)
    
    def parse(self, sql: str) -> Tuple[bool, str, Optional[exp.Expression]]:
        """Parse SQL for this dialect. Override in subclasses for dialect-specific parsing."""
        norm = normalize_sql(sql)
        try:
            tree = sqlglot.parse_one(norm, read=DIALECT_MAP.get(self.dialect, self.dialect))
            formatted = tree.sql(pretty=True, dialect=DIALECT_MAP.get(self.dialect, self.dialect))
            return True, formatted, tree
        except Exception:
            return False, norm, None
    
    def lint(self, sql: str, tree: exp.Expression) -> List[Issue]:
        """Run all rules and collect issues"""
        issues: List[Issue] = []
        for rule in self.rules:
            issue = rule.check(sql, tree, self.dialect)
            if issue:
                issues.append(issue)
        return issues
    
    def analyze(self, sql: str) -> Tuple[bool, str, Optional[exp.Expression], List[Issue]]:
        """Parse and lint SQL in one call"""
        parsed_ok, normalized_sql, tree = self.parse(sql)
        issues = self.lint(normalized_sql, tree) if parsed_ok and tree else []
        return parsed_ok, normalized_sql, tree, issues
