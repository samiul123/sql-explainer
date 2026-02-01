from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field

Dialect = Literal["postgres", "mysql", "sqlite", "tsql", "bigquery", "snowflake"]

class AnalyzeRequest(BaseModel):
    dialect: Dialect = "postgres"
    sql: str = Field(..., min_length=1)
    schema_text: Optional[str] = None  # optional: user can paste CREATE TABLE or bullet schema

class Issue(BaseModel):
    code: str
    severity: Literal["info", "warning", "critical"] = "warning"
    message: str
    evidence: Optional[str] = None

class Suggestion(BaseModel):
    title: str
    impact: Literal["low", "medium", "high"] = "medium"
    rationale: str
    actions: List[str] = Field(default_factory=list)
    index_sql: List[str] = Field(default_factory=list)       # optional CREATE INDEX statements
    rewrite_sql: Optional[str] = None                         # optional rewritten query
    caveats: List[str] = Field(default_factory=list)

class AnalyzeResponse(BaseModel):
    dialect: Dialect
    normalized_sql: str
    parsed: bool
    structure: Dict[str, Any] = Field(default_factory=dict)

    explanation: str
    breakdown: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)

    issues: List[Issue] = Field(default_factory=list)
    suggestions: List[Suggestion] = Field(default_factory=list)

    rewritten_sql: Optional[str] = None
    confidence: Literal["low", "medium", "high"] = "medium"
