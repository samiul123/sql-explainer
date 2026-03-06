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

# Automatically import all rule modules to trigger @register_rule() decorators
# This is done at the end to avoid circular import issues
from pathlib import Path as _Path
_rules_dir = _Path(__file__).parent.parent / "rules"
for _file in _rules_dir.glob("*.py"):
    if _file.name not in ("__init__.py", "base.py"):
        _module_name = _file.stem
        __import__(f"app.rules.{_module_name}")
