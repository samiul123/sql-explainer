from __future__ import annotations

import json
from typing import Any, Dict
from sqlglot import exp

from .dialects import get_linter
from .schemas import AnalyzeRequest, AnalyzeResponse
from .chains import build_explain_chain, build_optimize_chain, ExplainOutput, OptimizeOutput
from langchain_core.output_parsers import PydanticOutputParser

# Export commonly used functions
__all__ = [
    "get_linter",
    "extract_structure_for_llm",
    "analyze_sql",
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


def analyze_sql(req: AnalyzeRequest) -> AnalyzeResponse:
    """Main service function to analyze SQL with linting and LLM-based explanations/optimizations"""
    
    # Get cached linter and run complete analysis
    linter = get_linter(req.dialect)
    parsed_ok, normalized_sql, tree, issues = linter.analyze(req.sql)
    
    # Extract structure for LLM context
    structure = extract_structure_for_llm(tree) if tree else {}
    structure_json = json.dumps(structure, indent=2)
    issues_json = json.dumps([i.model_dump() for i in issues], indent=2)

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

    return AnalyzeResponse(
        dialect=req.dialect,
        normalized_sql=normalized_sql,
        parsed=parsed_ok,
        structure=structure,
        explanation=explain_out.explanation,
        breakdown=explain_out.breakdown,
        assumptions=explain_out.assumptions,
        issues=issues,
        suggestions=optimize_out.suggestions,
        rewritten_sql=optimize_out.rewritten_sql,
        confidence=confidence,
    )
