"""SQL dialect linters"""

from typing import Dict
from .base import DialectLinter, DIALECT_MAP, normalize_sql
from .postgres import PostgresLinter
from .mysql import MySQLLinter
from .sqlite import SQLiteLinter
from .tsql import TSQLLinter
from .bigquery import BigQueryLinter
from .snowflake import SnowflakeLinter

# Linter cache to avoid creating multiple instances
_linter_cache: Dict[str, DialectLinter] = {}


def get_linter(dialect: str) -> DialectLinter:
    """Factory function to get the appropriate linter for a dialect (cached)"""
    if dialect in _linter_cache:
        return _linter_cache[dialect]
    
    linters = {
        "postgres": PostgresLinter,
        "mysql": MySQLLinter,
        "sqlite": SQLiteLinter,
        "tsql": TSQLLinter,
        "bigquery": BigQueryLinter,
        "snowflake": SnowflakeLinter,
    }
    
    linter_class = linters.get(dialect, DialectLinter)
    linter = linter_class(dialect)
    _linter_cache[dialect] = linter
    return linter


__all__ = [
    "get_linter",
    "DialectLinter",
    "DIALECT_MAP",
    "normalize_sql",
    "PostgresLinter",
    "MySQLLinter",
    "SQLiteLinter",
    "TSQLLinter",
    "BigQueryLinter",
    "SnowflakeLinter",
]
