from __future__ import annotations

from typing import Optional
from abc import ABC, abstractmethod

from sqlglot import exp
from ..schemas import Issue


class Rule(ABC):
    """Base class for all linting rules"""
    
    @abstractmethod
    def check(self, sql: str, tree: exp.Expression, dialect: str) -> Optional[Issue]:
        """Check the SQL tree and return an Issue if found, None otherwise"""
        pass
