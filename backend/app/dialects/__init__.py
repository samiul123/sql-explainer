"""SQL dialect linters"""

from typing import Dict
from .base import DialectLinter, register_rule

# Linter cache to avoid creating multiple instances
_linter_cache: Dict[str, DialectLinter] = {}


def get_linter(dialect: str) -> DialectLinter:
    """Factory function to get the appropriate linter for a dialect (cached)"""
    if dialect in _linter_cache:
        return _linter_cache[dialect]
    
    linter = DialectLinter(dialect)
    _linter_cache[dialect] = linter
    return linter


__all__ = [
    "get_linter",
    "register_rule"
]
