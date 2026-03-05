from .base import DialectLinter


class MySQLLinter(DialectLinter):
    """MySQL-specific linter"""
    
    def _register_rules(self):
        super()._register_rules()
        # Add MySQL-specific rules here
