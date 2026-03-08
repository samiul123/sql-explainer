"""Detect redundant outer queries that don't perform any processing"""

from __future__ import annotations
from typing import List, Set, Optional, Tuple

from sqlglot import exp

from ..schemas import Issue
from ..dialects import register_rule
from .base import Rule


def get_subquery_from_select(select: exp.Select) -> Optional[Tuple[exp.Subquery, str]]:
    """
    Check if SELECT has a single subquery as its FROM source.
    Returns (subquery, alias) if found, None otherwise.
    """
    from_clause = select.args.get("from_")
    if not from_clause:
        return None
    
    # Get the source from FROM (it's in from_.this)
    source = from_clause.this
    
    # Check for joins - if there are joins, it's not a simple single source
    if list(select.find_all(exp.Join)):
        return None
    
    # Check if it's a subquery
    if isinstance(source, exp.Subquery):
        alias = source.alias or ""
        return (source, alias)
    
    return None


def get_cte_reference(select: exp.Select, cte_names: Set[str]) -> Optional[str]:
    """
    Check if SELECT references a single CTE.
    Returns CTE name if found, None otherwise.
    """
    from_clause = select.args.get("from_")
    if not from_clause:
        return None
    
    source = from_clause.this
    
    # Check for joins
    if list(select.find_all(exp.Join)):
        return None
    
    if isinstance(source, exp.Table):
        table_name = source.name
        if table_name in cte_names:
            return table_name
    
    return None


def has_joins(select: exp.Select) -> bool:
    """Check if SELECT has any JOIN clauses"""
    return len(list(select.find_all(exp.Join))) > 0


def has_window_functions(select: exp.Select) -> bool:
    """Check if SELECT has any window functions"""
    for expr in select.expressions:
        if expr.find(exp.Window):
            return True
    return False


def is_simple_column_ref(expr: exp.Expression) -> bool:
    """Check if expression is a simple column reference (no transformations)"""
    # Handle aliased columns
    if isinstance(expr, exp.Alias):
        inner = expr.this
        return isinstance(inner, exp.Column)
    
    # Direct column reference
    if isinstance(expr, exp.Column):
        return True
    
    # Star is also "simple" for our purposes
    if isinstance(expr, exp.Star):
        return True
    
    return False


def all_columns_are_passthrough(select: exp.Select) -> bool:
    """Check if all SELECT expressions are simple column refs (passthrough)"""
    # SELECT * is passthrough
    if select.is_star:
        return True
    
    # Check each expression
    for expr in select.expressions:
        if not is_simple_column_ref(expr):
            return False
    
    return True


def get_order_by_sql(select: exp.Select) -> Optional[str]:
    """Get normalized ORDER BY clause SQL for comparison"""
    order = select.args.get("order")
    if order:
        return order.sql()
    return None


def get_limit_value(select: exp.Select) -> Optional[int]:
    """Get LIMIT value if present"""
    limit = select.args.get("limit")
    if limit and isinstance(limit, exp.Limit):
        # LIMIT uses .expression for the value, not .this
        limit_expr = limit.expression
        if isinstance(limit_expr, exp.Literal) and limit_expr.is_int:
            return int(limit_expr.this)
    return None


def is_outer_query_redundant(outer: exp.Select, inner: exp.Select) -> Tuple[bool, str]:
    """
    Check if outer SELECT is redundant wrapper around inner SELECT.
    Returns (is_redundant, reason).
    """
    # Check for WHERE clause
    if outer.args.get("where"):
        return False, ""
    
    # Check for HAVING clause
    if outer.args.get("having"):
        return False, ""
    
    # Check for GROUP BY clause
    if outer.args.get("group"):
        return False, ""
    
    # Check for JOINs
    if has_joins(outer):
        return False, ""
    
    # Check for DISTINCT (if inner doesn't have it)
    outer_distinct = outer.args.get("distinct")
    inner_distinct = inner.args.get("distinct") if inner else None
    if outer_distinct and not inner_distinct:
        return False, ""
    
    # Check for window functions
    if has_window_functions(outer):
        return False, ""
    
    # Check for LIMIT (if different from inner or inner has none)
    outer_limit = get_limit_value(outer)
    inner_limit = get_limit_value(inner) if inner else None
    if outer_limit is not None:
        if inner_limit is None or outer_limit != inner_limit:
            return False, ""
    
    # Check for ORDER BY (if different from inner)
    outer_order = get_order_by_sql(outer)
    inner_order = get_order_by_sql(inner) if inner else None
    if outer_order is not None:
        if inner_order is None or outer_order != inner_order:
            return False, ""
    
    # Check for OFFSET
    if outer.args.get("offset"):
        inner_offset = inner.args.get("offset") if inner else None
        if not inner_offset:
            return False, ""
    
    # Check if columns are passthrough (no transformations)
    if not all_columns_are_passthrough(outer):
        return False, ""
    
    return True, "passes through results unchanged"


def count_redundant_layers(select: exp.Select) -> int:
    """Count how many redundant wrapper layers exist"""
    count = 0
    current = select
    
    while True:
        result = get_subquery_from_select(current)
        if not result:
            break
        
        subquery, _ = result
        inner_select = subquery.this
        
        if not isinstance(inner_select, exp.Select):
            break
        
        is_redundant, _ = is_outer_query_redundant(current, inner_select)
        if not is_redundant:
            break
        
        count += 1
        current = inner_select
    
    return count


@register_rule()
class RedundantOuterQueryRule(Rule):
    """Detect unnecessary outer SELECT wrapping subqueries/CTEs"""
    
    def check(self, sql: str, tree: exp.Expression, dialect: str) -> List[Issue]:
        issues: List[Issue] = []
        processed_selects: Set[int] = set()  # Track by id to avoid duplicates
        
        # Get all CTE names for CTE detection
        cte_names: Set[str] = set()
        cte_map: dict = {}  # Map CTE name to its SELECT
        with_clause = tree.args.get("with_")
        if with_clause:
            for cte in with_clause.find_all(exp.CTE):
                cte_name = cte.alias
                cte_names.add(cte_name)
                if isinstance(cte.this, exp.Select):
                    cte_map[cte_name] = cte.this
        
        # Find all SELECT statements
        for select in tree.find_all(exp.Select):
            select_id = id(select)
            
            # Skip if already processed (inner selects of redundant queries)
            if select_id in processed_selects:
                continue
            
            # Check for subquery wrapper
            subquery_result = get_subquery_from_select(select)
            if subquery_result:
                subquery, alias = subquery_result
                inner_select = subquery.this
                
                if isinstance(inner_select, exp.Select):
                    is_redundant, reason = is_outer_query_redundant(select, inner_select)
                    
                    if is_redundant:
                        # Count total redundant layers
                        layer_count = count_redundant_layers(select)
                        
                        # Mark inner selects as processed
                        current = select
                        for _ in range(layer_count):
                            result = get_subquery_from_select(current)
                            if result:
                                inner = result[0].this
                                processed_selects.add(id(inner))
                                current = inner
                        
                        # Build message
                        if layer_count > 1:
                            message = f"Outer SELECT has {layer_count} redundant wrapper layers. Simplify by removing unnecessary nesting."
                        else:
                            alias_text = f" '{alias}'" if alias else ""
                            message = f"Outer SELECT{alias_text} is redundant; it {reason}. Consider removing the wrapper."
                        
                        # Build evidence (truncate if too long)
                        evidence = select.sql()[:120]
                        if len(select.sql()) > 120:
                            evidence += "..."
                        
                        issues.append(Issue(
                            code="REDUNDANT_OUTER_QUERY",
                            severity="info",
                            message=message,
                            evidence=evidence
                        ))
                        continue
            
            # Check for CTE wrapper
            cte_ref = get_cte_reference(select, cte_names)
            if cte_ref and cte_ref in cte_map:
                inner_select = cte_map[cte_ref]
                is_redundant, reason = is_outer_query_redundant(select, inner_select)
                
                if is_redundant:
                    # Check if CTE is only used once (truly redundant)
                    cte_usage_count = sum(
                        1 for t in tree.find_all(exp.Table) 
                        if t.name == cte_ref
                    )
                    
                    if cte_usage_count == 1:
                        message = f"CTE '{cte_ref}' is used once with passthrough SELECT. Consider inlining the CTE."
                        
                        evidence = select.sql()[:120]
                        if len(select.sql()) > 120:
                            evidence += "..."
                        
                        issues.append(Issue(
                            code="REDUNDANT_OUTER_QUERY",
                            severity="info",
                            message=message,
                            evidence=evidence
                        ))
        
        return issues
