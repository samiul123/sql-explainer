from __future__ import annotations

from typing import List
from abc import ABC, abstractmethod

from sqlglot import exp
from ..schemas import Issue


class Rule(ABC):
    """Base class for all linting rules"""
    
    @abstractmethod
    def check(self, sql: str, tree: exp.Expression, dialect: str) -> List[Issue]:
        """Check the SQL tree and return a list of Issues found (empty if none)"""
        pass
