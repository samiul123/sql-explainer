from .base import DialectLinter


class BigQueryLinter(DialectLinter):
    """BigQuery-specific linter"""
    
    def _register_rules(self):
        super()._register_rules()
