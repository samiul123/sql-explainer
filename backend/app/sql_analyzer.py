from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
import sqlglot
from sqlglot import exp

from .dialects import get_linter
from .schemas import AnalyzeRequest, AnalyzeResponse
from .chains import build_explain_chain, build_optimize_chain, ExplainOutput, OptimizeOutput
from langchain_core.output_parsers import PydanticOutputParser

# Export commonly used functions
__all__ = [
    "get_linter",
    "extract_structure_for_llm",
    "generate_logical_sequence",
    "analyze_sql",
    "prettify_sql",
]


def prettify_sql(sql: Optional[str], dialect: str = "postgres") -> Optional[str]:
    """Pretty-print SQL using sqlglot. Returns original if formatting fails."""
    if not sql:
        return sql
    try:
        return sqlglot.transpile(sql, read=dialect, pretty=True)[0]
    except Exception:
        return sql  # Return original if parsing fails


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


def generate_logical_sequence(tree: exp.Expression) -> List[Dict[str, Any]]:
    """Generate logical SQL execution sequence (conceptual order)"""
    if tree is None:
        return []
    
    steps = []
    step_num = 1
    
    # 1. WITH (CTEs) - evaluated first
    if tree.args.get("with"):
        for cte in tree.find_all(exp.CTE):
            steps.append({
                "step": step_num,
                "clause": "WITH (CTE)",
                "description": f"Define temporary result set: {cte.alias_or_name}",
                "sql": cte.sql()
            })
            step_num += 1
    
    # 2. FROM - identify data sources
    tables = list(tree.find_all(exp.Table))
    if tables:
        table_names = ', '.join(t.name for t in tables)
        steps.append({
            "step": step_num,
            "clause": "FROM",
            "description": f"Get rows from table(s): {table_names}",
            "sql": ', '.join(t.sql() for t in tables)
        })
        step_num += 1
    
    # 3. JOIN - combine tables
    joins = list(tree.find_all(exp.Join))
    for join in joins:
        join_kind = join.args.get('kind', 'INNER')
        join_table = join.this.sql() if join.this else ''
        steps.append({
            "step": step_num,
            "clause": "JOIN",
            "description": f"{join_kind} JOIN with {join_table}",
            "sql": join.sql()
        })
        step_num += 1
    
    # 4. WHERE - filter rows
    where_clause = tree.args.get("where")
    if where_clause:
        steps.append({
            "step": step_num,
            "clause": "WHERE",
            "description": "Filter rows based on condition",
            "sql": where_clause.sql()
        })
        step_num += 1
    
    # 5. GROUP BY - group rows
    group_clause = tree.args.get("group")
    if group_clause:
        steps.append({
            "step": step_num,
            "clause": "GROUP BY",
            "description": "Group rows by specified columns",
            "sql": group_clause.sql()
        })
        step_num += 1
    
    # 6. HAVING - filter groups
    having_clause = tree.args.get("having")
    if having_clause:
        steps.append({
            "step": step_num,
            "clause": "HAVING",
            "description": "Filter groups based on aggregate condition",
            "sql": having_clause.sql()
        })
        step_num += 1
    
    # 7. SELECT - project columns
    # Get only the expressions from the SELECT clause itself (columns, aliases, aggregates)
    select_exprs = tree.expressions if hasattr(tree, 'expressions') else []
    if select_exprs:
        cols = select_exprs[:5]  # Show first 5
        cols_str = ", ".join(col.sql() for col in cols)
        if len(select_exprs) > 5:
            cols_str += ", ..."
        steps.append({
            "step": step_num,
            "clause": "SELECT",
            "description": "Select and compute final columns",
            "sql": f"SELECT {cols_str}"
        })
        step_num += 1
    
    # 8. DISTINCT - remove duplicates
    if tree.args.get("distinct"):
        steps.append({
            "step": step_num,
            "clause": "DISTINCT",
            "description": "Remove duplicate rows from result set",
            "sql": "DISTINCT"
        })
        step_num += 1
    
    # 9. ORDER BY - sort results
    # 9. ORDER BY - sort results
    order_clause = tree.args.get("order")
    if order_clause:
        # Extract just column names and direction (ASC/DESC) without NULLS FIRST/LAST
        order_items = []
        for ordered_expr in order_clause.expressions:
            # Get the column/expression being ordered
            col_sql = ordered_expr.this.sql() if hasattr(ordered_expr, 'this') else str(ordered_expr)
            
            # Add DESC if specified (ASC is default, usually omitted)
            if hasattr(ordered_expr, 'args') and ordered_expr.args.get('desc'):
                col_sql += " DESC"
            
            order_items.append(col_sql)
        
        steps.append({
            "step": step_num,
            "clause": "ORDER BY",
            "description": "Sort results by specified columns",
            "sql": f"ORDER BY {', '.join(order_items)}"
        })
        step_num += 1
    
    # 10. LIMIT/OFFSET - limit output
    limit_clause = tree.args.get("limit")
    if limit_clause:
        steps.append({
            "step": step_num,
            "clause": "LIMIT",
            "description": "Limit number of results returned",
            "sql": limit_clause.sql()
        })
        step_num += 1
    
    return steps


def analyze_sql(req: AnalyzeRequest) -> AnalyzeResponse:
    """Main service function to analyze SQL with linting and LLM-based explanations/optimizations"""
    
    # Get cached linter and run complete analysis
    linter = get_linter(req.dialect)
    parsed_ok, normalized_sql, tree, issues = linter.analyze(req.sql)
    
    # Extract structure for LLM context
    structure = extract_structure_for_llm(tree) if tree else {}
    structure_json = json.dumps(structure, indent=2)
    issues_json = json.dumps([i.model_dump() for i in issues], indent=2)
    
    # Generate logical execution sequence
    execution_sequence = generate_logical_sequence(tree) if tree else []

    # Build chains
    explain_chain = build_explain_chain()
    optimize_chain = build_optimize_chain()
    explain_parser = PydanticOutputParser(pydantic_object=ExplainOutput)
    optimize_parser = PydanticOutputParser(pydantic_object=OptimizeOutput)

    # Get explanation from LLM
    explain_out = explain_chain.invoke({
        "dialect": req.dialect,
        "sql": normalized_sql,
        "structure_json": structure_json,
        "schema_text": req.schema_text or "",
        "format_instructions": explain_parser.get_format_instructions(),
    })

    # Get optimization suggestions from LLM
    optimize_out = optimize_chain.invoke({
        "dialect": req.dialect,
        "sql": normalized_sql,
        "structure_json": structure_json,
        "issues_json": issues_json,
        "schema_text": req.schema_text or "",
        "format_instructions": optimize_parser.get_format_instructions(),
    })

    # Determine overall confidence
    confidence = (
        "low" if ("low" in (explain_out.confidence, optimize_out.confidence))
        else "high" if ("high" in (explain_out.confidence, optimize_out.confidence))
        else "medium"
    )

    # Prettify SQL in suggestions
    for suggestion in optimize_out.suggestions:
        if suggestion.rewrite_sql:
            suggestion.rewrite_sql = prettify_sql(suggestion.rewrite_sql, req.dialect)

    return AnalyzeResponse(
        dialect=req.dialect,
        normalized_sql=normalized_sql,
        parsed=parsed_ok,
        structure=structure,
        execution_sequence=execution_sequence,
        explanation=explain_out.explanation,
        breakdown=explain_out.breakdown,
        assumptions=explain_out.assumptions,
        issues=issues,
        suggestions=optimize_out.suggestions,
        rewritten_sql=prettify_sql(optimize_out.rewritten_sql, req.dialect),
        confidence=confidence,
    )
