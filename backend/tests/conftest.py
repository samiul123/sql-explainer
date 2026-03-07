"""Shared fixtures for all tests"""

import pytest
import sqlglot
from sqlglot import exp


@pytest.fixture
def parse():
    """Fixture to parse SQL into AST"""
    def _parse(sql: str, dialect: str = "postgres") -> exp.Expression:
        return sqlglot.parse_one(sql, read=dialect)
    return _parse


@pytest.fixture
def linter():
    """Fixture to get a linter instance"""
    from app.dialects import get_linter
    def _linter(dialect: str = "postgres"):
        return get_linter(dialect)
    return _linter
