from __future__ import annotations

import json
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .schemas import AnalyzeRequest, AnalyzeResponse
from .sql_analyzer import parse_sql, lint_sql
from .chains import build_explain_chain, build_optimize_chain, ExplainOutput, OptimizeOutput
from langchain_core.output_parsers import PydanticOutputParser

load_dotenv()

app = FastAPI(title="SQL Explain + Optimize API", version="0.1.0")

allowed = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[a.strip() for a in allowed if a.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

explain_chain = build_explain_chain()
optimize_chain = build_optimize_chain()
explain_parser = PydanticOutputParser(pydantic_object=ExplainOutput)
optimize_parser = PydanticOutputParser(pydantic_object=OptimizeOutput)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    parsed_ok, normalized_sql, structure = parse_sql(req.sql, req.dialect)
    issues = lint_sql(normalized_sql, req.dialect, structure) if parsed_ok else []

    structure_json = json.dumps(structure, indent=2)
    issues_json = json.dumps([i.model_dump() for i in issues], indent=2)

    explain_out = explain_chain.invoke({
        "dialect": req.dialect,
        "sql": normalized_sql,
        "structure_json": structure_json,
        "schema_text": req.schema_text or "",
        "format_instructions": explain_parser.get_format_instructions(),
    })

    optimize_out = optimize_chain.invoke({
        "dialect": req.dialect,
        "sql": normalized_sql,
        "structure_json": structure_json,
        "issues_json": issues_json,
        "schema_text": req.schema_text or "",
        "format_instructions": optimize_parser.get_format_instructions(),
    })

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

        confidence=(
            "low" if ("low" in (explain_out.confidence, optimize_out.confidence))
            else "high" if ("high" in (explain_out.confidence, optimize_out.confidence))
            else "medium"
        ),
    )
