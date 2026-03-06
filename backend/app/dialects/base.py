from __future__ import annotations

from typing import List, Tuple, Optional, Type, Dict
import re

import sqlglot
from sqlglot import exp

from ..schemas import Issue
from ..rules import Rule

DIALECT_MAP = {
    "postgres": "postgres",
    "mysql": "mysql",
    "sqlite": "sqlite",
    "tsql": "tsql",
    "bigquery": "bigquery",
    "snowflake": "snowflake",
}

# Global registry mapping dialect names to rule classes
_rule_registry: Dict[str, List[Type[Rule]]] = {}


def register_rule(dialects: Optional[List[str]] = None, exclude: Optional[List[str]] = None):
    """Decorator to register a rule class for specific dialects.
    
    Args:
        dialects: List of dialect names to register for. If None, registers for all dialects.
        exclude: List of dialect names to exclude. Only used when dialects is None.
    
    Examples:
        @register_rule()  # All dialects
        class MyRule(Rule): ...
        
        @register_rule(dialects=["postgres", "mysql"])  # Specific dialects
        class PostgresSpecificRule(Rule): ...
        
        @register_rule(exclude=["sqlite"])  # All except sqlite
        class ComplexRule(Rule): ...
    """
    def decorator(rule_cls: Type[Rule]) -> Type[Rule]:
        # Determine target dialects
        all_dialects = list(DIALECT_MAP.keys())
        
        if dialects is not None:
            target_dialects = dialects
        elif exclude is not None:
            target_dialects = [d for d in all_dialects if d not in exclude]
        else:
            target_dialects = all_dialects
        
        # Register the rule class for each target dialect
        for dialect in target_dialects:
            if dialect not in _rule_registry:
                _rule_registry[dialect] = []
            _rule_registry[dialect].append(rule_cls)
        
        return rule_cls
    return decorator


def get_rules_for_dialect(dialect: str) -> List[Type[Rule]]:
    """Get all rule classes registered for a specific dialect."""
    return _rule_registry.get(dialect, [])


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
        """Register all rules for this dialect from the registry"""
        rule_classes = get_rules_for_dialect(self.dialect)
        for rule_class in rule_classes:
            self.add_rule(rule_class())
    
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
