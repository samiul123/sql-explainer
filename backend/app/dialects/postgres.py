from .base import DialectLinter


class PostgresLinter(DialectLinter):
    """PostgreSQL-specific linter"""
    
    def _register_rules(self):
        super()._register_rules()
        # Add Postgres-specific rules here
