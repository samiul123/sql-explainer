from .base import DialectLinter


class TSQLLinter(DialectLinter):
    """T-SQL (SQL Server)-specific linter"""
    
    def _register_rules(self):
        super()._register_rules()
