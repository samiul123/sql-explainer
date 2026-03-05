from .base import DialectLinter


class SnowflakeLinter(DialectLinter):
    """Snowflake-specific linter"""
    
    def _register_rules(self):
        super()._register_rules()
