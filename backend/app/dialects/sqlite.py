from .base import DialectLinter


class SQLiteLinter(DialectLinter):
    """SQLite-specific linter"""
    
    def _register_rules(self):
        super()._register_rules()
