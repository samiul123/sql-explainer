"""Detect opportunities to push WHERE filters into subqueries/CTEs"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Set, Optional

from sqlglot import exp

from ..schemas import Issue
from ..dialects import register_rule
from .base import Rule


@dataclass
class PushdownOpportunity:
    """Represents a filter that could be pushed into a subquery/CTE"""
    column: str
    filter_sql: str
    target_name: str  # subquery alias or CTE name
    target_type: str  # 'subquery' or 'CTE'


def get_computed_columns(select_node: exp.Select) -> Set[str]:
    """Get columns that are computed/derived (not simple column refs)"""
    computed: Set[str] = set()
    
    select_expressions = select_node.args.get("expressions", [])
    for expr in select_expressions:
        alias = None
        
        if isinstance(expr, exp.Alias):
            alias = expr.alias
            inner = expr.this
            # If inner is not a simple column, it's computed
            if not isinstance(inner, exp.Column):
                computed.add(alias)
        elif hasattr(expr, 'alias') and expr.alias:
            # Expression with alias that's not exp.Alias
            alias = expr.alias
            computed.add(alias)
    
    return computed


def get_aggregate_columns(select_node: exp.Select) -> Set[str]:
    """Get columns that are aggregate results"""
    aggregates: Set[str] = set()
    
    select_expressions = select_node.args.get("expressions", [])
    for expr in select_expressions:
        alias = None
        inner = expr
        
        if isinstance(expr, exp.Alias):
            alias = expr.alias
            inner = expr.this
        elif hasattr(expr, 'alias') and expr.alias:
            alias = expr.alias
        
        # Check if expression contains aggregate function
        has_agg = bool(
            inner.find(exp.Count) or
            inner.find(exp.Sum) or
            inner.find(exp.Avg) or
            inner.find(exp.Max) or
            inner.find(exp.Min) or
            inner.find(exp.AggFunc)
        )
        
        if has_agg and alias:
            aggregates.add(alias)
    
    return aggregates


def get_inner_filter_predicates(where_node: Optional[exp.Where]) -> dict[str, Set[str]]:
    """
    Extract filter predicates from WHERE clause.
    Returns dict: column_name -> set of normalized filter values (without table prefix)
    """
    predicates: dict[str, Set[str]] = {}
    
    if not where_node:
        return predicates
    
    comparison_types = (
        exp.EQ, exp.NEQ, exp.GT, exp.GTE, exp.LT, exp.LTE,
        exp.In, exp.Like, exp.ILike, exp.Between
    )
    
    for node in where_node.walk():
        if isinstance(node, comparison_types):
            left = getattr(node, "this", None)
            right = getattr(node, "expression", None)
            if isinstance(left, exp.Column):
                col_name = left.name
                # Normalize: store just the right-side value for comparison
                right_sql = right.sql() if right else ""
                op_type = type(node).__name__
                normalized_key = f"{op_type}:{right_sql}"
                
                if col_name not in predicates:
                    predicates[col_name] = set()
                predicates[col_name].add(normalized_key)
    
    return predicates


def extract_outer_filter_columns(
    where_node: exp.Where,
    target_alias: str
) -> List[tuple[str, str, str]]:
    """
    Extract columns from outer WHERE that reference the target (subquery/CTE alias).
    Returns list of (column_name, filter_sql, normalized_key)
    """
    filters: List[tuple[str, str, str]] = []
    
    comparison_types = (
        exp.EQ, exp.NEQ, exp.GT, exp.GTE, exp.LT, exp.LTE,
        exp.In, exp.Like, exp.ILike, exp.Between
    )
    
    for node in where_node.walk():
        if isinstance(node, comparison_types):
            left = getattr(node, "this", None)
            right = getattr(node, "expression", None)
            if isinstance(left, exp.Column):
                col_table = left.table or ""
                if col_table == target_alias or not col_table:
                    # Normalize: same format as inner predicates
                    right_sql = right.sql() if right else ""
                    op_type = type(node).__name__
                    normalized_key = f"{op_type}:{right_sql}"
                    filters.append((left.name, node.sql(), normalized_key))
    
    return filters


def analyze_subquery(
    subquery: exp.Subquery,
    outer_where: exp.Where
) -> List[PushdownOpportunity]:
    """Analyze a subquery for pushdown opportunities"""
    opportunities: List[PushdownOpportunity] = []
    
    # Get subquery alias
    alias = subquery.alias
    if not alias:
        return opportunities
    
    # Get inner SELECT
    inner_select = subquery.find(exp.Select)
    if not inner_select:
        return opportunities
    
    # Get what can't be pushed: computed and aggregate columns
    computed_cols = get_computed_columns(inner_select)
    aggregate_cols = get_aggregate_columns(inner_select)
    unpushable = computed_cols | aggregate_cols
    
    # Get existing inner filters
    inner_where = inner_select.args.get("where")
    inner_predicates = get_inner_filter_predicates(inner_where)
    
    # Get outer filters referencing this subquery
    outer_filters = extract_outer_filter_columns(outer_where, alias)
    
    # Track columns we've already flagged to avoid duplicates
    flagged_columns: Set[str] = set()
    
    # Find pushable filters
    for col_name, filter_sql, normalized_key in outer_filters:
        # Skip if column is computed/aggregated (can't push)
        if col_name in unpushable:
            continue
        
        # Skip if semantically same filter already exists inside
        if col_name in inner_predicates and normalized_key in inner_predicates[col_name]:
            continue
        
        # Skip if we already flagged this column
        if col_name in flagged_columns:
            continue
        
        flagged_columns.add(col_name)
        
        # This filter could potentially be pushed down
        opportunities.append(PushdownOpportunity(
            column=col_name,
            filter_sql=filter_sql,
            target_name=alias,
            target_type="subquery"
        ))
    
    return opportunities


def analyze_cte(
    cte: exp.CTE,
    outer_where: exp.Where,
    main_query: exp.Expression
) -> List[PushdownOpportunity]:
    """Analyze a CTE for pushdown opportunities"""
    opportunities: List[PushdownOpportunity] = []
    
    # Get CTE name
    cte_name = cte.alias
    if not cte_name:
        return opportunities
    
    # Get inner SELECT
    inner_select = cte.find(exp.Select)
    if not inner_select:
        return opportunities
    
    # Check if main query actually uses this CTE
    cte_referenced = False
    for table in main_query.find_all(exp.Table):
        if table.name == cte_name:
            cte_referenced = True
            break
    
    if not cte_referenced:
        return opportunities
    
    # Get what can't be pushed
    computed_cols = get_computed_columns(inner_select)
    aggregate_cols = get_aggregate_columns(inner_select)
    unpushable = computed_cols | aggregate_cols
    
    # Get existing inner filters
    inner_where = inner_select.args.get("where")
    inner_predicates = get_inner_filter_predicates(inner_where)
    
    # Get outer filters referencing this CTE
    outer_filters = extract_outer_filter_columns(outer_where, cte_name)
    
    # Track columns we've already flagged
    flagged_columns: Set[str] = set()
    
    # Find pushable filters
    for col_name, filter_sql, normalized_key in outer_filters:
        if col_name in unpushable:
            continue
        
        if col_name in inner_predicates and normalized_key in inner_predicates[col_name]:
            continue
        
        if col_name in flagged_columns:
            continue
        
        flagged_columns.add(col_name)
        
        opportunities.append(PushdownOpportunity(
            column=col_name,
            filter_sql=filter_sql,
            target_name=cte_name,
            target_type="CTE"
        ))
    
    return opportunities


@register_rule()
class SubqueryPushdownRule(Rule):
    """Detect opportunities to push WHERE filters into subqueries/CTEs"""

    def check(self, sql: str, tree: exp.Expression, dialect: str) -> List[Issue]:
        issues: List[Issue] = []
        
        # Get outer WHERE clause
        outer_where = tree.args.get("where")
        if not outer_where:
            return []
        
        # Analyze subqueries
        for subquery in tree.find_all(exp.Subquery):
            opportunities = analyze_subquery(subquery, outer_where)
            for opp in opportunities:
                issues.append(Issue(
                    code="SUBQUERY_PUSHDOWN_OPPORTUNITY",
                    severity="info",
                    message=f"Filter '{opp.filter_sql}' could be pushed into subquery '{opp.target_name}' to reduce rows before materialization",
                    evidence=f"Add WHERE {opp.column} condition inside the subquery"
                ))
        
        # Analyze CTEs
        with_clause = tree.args.get("with_")
        if with_clause:
            for cte in with_clause.find_all(exp.CTE):
                opportunities = analyze_cte(cte, outer_where, tree)
                for opp in opportunities:
                    issues.append(Issue(
                        code="CTE_PUSHDOWN_OPPORTUNITY",
                        severity="info",
                        message=f"Filter '{opp.filter_sql}' could be pushed into CTE '{opp.target_name}' to reduce rows before materialization",
                        evidence=f"Add WHERE {opp.column} condition inside the CTE"
                    ))
        
        return issues
