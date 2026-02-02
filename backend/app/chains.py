from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from .schemas import Suggestion

class ExplainOutput(BaseModel):
    explanation: str = Field(..., description="Plain-English explanation of what the SQL does.")
    breakdown: List[str] = Field(default_factory=list, description="Step-by-step breakdown of clauses.")
    assumptions: List[str] = Field(default_factory=list, description="Assumptions made due to missing schema/stats.")
    confidence: str = Field(..., description="low|medium|high")

class OptimizeOutput(BaseModel):
    suggestions: List[Suggestion] = Field(default_factory=list)
    rewritten_sql: Optional[str] = None
    confidence: Optional[str] = Field("medium", description="low|medium|high")

def get_llm() -> ChatOllama:
    model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    return ChatOllama(
        model=model,
        base_url=base_url,
        temperature=0.0,
    )

def build_explain_chain():
    parser = PydanticOutputParser(pydantic_object=ExplainOutput)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a senior database engineer. Explain SQL accurately and clearly.\n"
         "Be dialect-aware. Do not invent tables/columns.\n"
         "If schema is missing, state assumptions explicitly.\n"
         "Return ONLY valid JSON.\n"
         "{format_instructions}"),
        ("human",
         "Dialect: {dialect}\n\n"
         "SQL:\n{sql}\n\n"
         "Extracted structure (from parser):\n{structure_json}\n\n"
         "Schema (optional):\n{schema_text}\n")
    ])

    return prompt | get_llm() | parser

def build_optimize_chain():
    parser = PydanticOutputParser(pydantic_object=OptimizeOutput)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a senior database performance engineer. Provide safe, practical optimization advice.\n"
         "Prioritize highest impact. Suggest indexes when appropriate.\n"
         "If you propose a rewrite, keep semantics the same.\n"
         "If uncertain without EXPLAIN/stats, label caveats.\n"
         "Return ONLY valid JSON.\n"
         "{format_instructions}"),
        ("human",
         "Dialect: {dialect}\n\n"
         "SQL:\n{sql}\n\n"
         "Extracted structure:\n{structure_json}\n\n"
         "Detected issues:\n{issues_json}\n\n"
         "Schema (optional):\n{schema_text}\n\n"
         "Guidelines:\n"
         "- Provide 3 to 8 suggestions.\n"
         "- Include index SQL statements if helpful.\n"
         "- Provide rewritten_sql only if you are confident it parses in the dialect.\n"
         "- MUST include a 'confidence' field (low/medium/high) for your overall assessment.\n")
    ])

    return prompt | get_llm() | parser
