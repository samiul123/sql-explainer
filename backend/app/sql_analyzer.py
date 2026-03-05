from __future__ import annotations

from typing import Any, Dict
from sqlglot import exp

# Import the factory function and utilities from dialects
from .dialects import get_linter

# Export commonly used functions for backward compatibility
__all__ = [
    "get_linter",
    "extract_structure_for_llm",
]


def extract_structure_for_llm(tree: exp.Expression) -> Dict[str, Any]:
    """Extract structure info from tree for LLM context"""
    if tree is None:
        return {}
    
    structure: Dict[str, Any] = {
        "tables": sorted({t.name for t in tree.find_all(exp.Table)}),
        "columns": sorted({c.sql() for c in tree.find_all(exp.Column)}),
        "has_where": tree.args.get("where") is not None,
        "has_group_by": tree.args.get("group") is not None,
        "has_having": tree.args.get("having") is not None,
        "has_order_by": tree.args.get("order") is not None,
        "has_limit": tree.args.get("limit") is not None,
        "joins": [],
        "ctes": [],
    }

    # joins
    for j in tree.find_all(exp.Join):
        on_clause = j.args.get("on")
        structure["joins"].append({
            "kind": (j.args.get("kind") or "JOIN").upper(),
            "this": j.this.sql() if j.this else None,
            "on": on_clause.sql() if on_clause else None,
        })

    # ctes
    with_ = tree.args.get("with")
    if with_:
        for cte in with_.find_all(exp.CTE):
            structure["ctes"].append(cte.alias_or_name)

    return structure
