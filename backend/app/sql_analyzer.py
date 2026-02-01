from __future__ import annotations

from typing import Any, Dict, List, Tuple
import re

import sqlglot
from sqlglot import exp

from .schemas import Issue

DIALECT_MAP = {
    "postgres": "postgres",
    "mysql": "mysql",
    "sqlite": "sqlite",
    "tsql": "tsql",
    "bigquery": "bigquery",
    "snowflake": "snowflake",
}

def normalize_sql(sql: str) -> str:
    # basic cleanup
    sql = sql.strip()
    # collapse excessive whitespace but keep line breaks somewhat
    sql = re.sub(r"[ \t]+", " ", sql)
    return sql

def parse_sql(sql: str, dialect: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Returns: (parsed_ok, normalized_sql, structure_json)
    """
    norm = normalize_sql(sql)

    try:
        tree = sqlglot.parse_one(norm, read=DIALECT_MAP.get(dialect, dialect))
    except Exception:
        return False, norm, {}

    # Build a compact structure summary
    structure: Dict[str, Any] = {
        "tables": sorted({t.name for t in tree.find_all(exp.Table)}),
        "columns": sorted({c.sql() for c in tree.find_all(exp.Column)}),
        "has_where": tree.args.get("where") is not None,
        "has_group_by": tree.args.get("group") is not None,
        "has_order_by": tree.args.get("order") is not None,
        "has_limit": tree.args.get("limit") is not None,
        "joins": [],
        "ctes": [],
        "functions_in_where": [],
        "select_star": False,
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
            alias = cte.alias_or_name
            structure["ctes"].append(alias)

    # select *
    for s in tree.find_all(exp.Star):
        structure["select_star"] = True
        break

    # functions in where
    where = tree.args.get("where")
    if where:
        for func in where.find_all(exp.Func):
            structure["functions_in_where"].append(func.sql())

    return True, tree.sql(pretty=True, dialect=DIALECT_MAP.get(dialect, dialect)), structure

def lint_sql(sql: str, dialect: str, structure: Dict[str, Any]) -> List[Issue]:
    issues: List[Issue] = []
    s = sql.lower()

    # Rule 1: SELECT *
    if structure.get("select_star"):
        issues.append(Issue(
            code="SELECT_STAR",
            severity="warning",
            message="Avoid SELECT * in production queries; select only needed columns.",
            evidence="SELECT *"
        ))

    # Rule 2: Missing LIMIT (simple heuristic)
    if structure.get("has_limit") is False and "select" in s and "count(" not in s:
        issues.append(Issue(
            code="NO_LIMIT",
            severity="info",
            message="Query has no LIMIT. For exploration or large tables, consider adding LIMIT.",
        ))

    # Rule 3: Leading wildcard LIKE
    if re.search(r"like\s+'%[^']*'", s):
        issues.append(Issue(
            code="LEADING_WILDCARD_LIKE",
            severity="warning",
            message="Leading wildcard LIKE (e.g., LIKE '%foo') usually prevents index usage.",
        ))

    # Rule 4: OR-heavy filters (rough)
    if " where " in s and " or " in s:
        issues.append(Issue(
            code="OR_IN_WHERE",
            severity="info",
            message="OR conditions can reduce index effectiveness; consider UNION ALL or refactoring if performance is an issue.",
        ))

    # Rule 5: Functions in WHERE
    if structure.get("functions_in_where"):
        issues.append(Issue(
            code="FUNCTION_IN_WHERE",
            severity="warning",
            message="Functions in WHERE can prevent index usage (e.g., DATE(col), LOWER(col)). Consider rewriting predicates.",
            evidence="; ".join(structure["functions_in_where"][:3])
        ))

    # Rule 6: JOIN without ON (cartesian risk)
    for j in structure.get("joins", []):
        if j.get("on") is None and j.get("kind") not in ("CROSS", "CROSS JOIN"):
            issues.append(Issue(
                code="JOIN_WITHOUT_ON",
                severity="critical",
                message="JOIN without ON can create a cartesian product (huge result set).",
                evidence=str(j)
            ))
            break

    # Rule 7: DISTINCT as band-aid
    if "select distinct" in s:
        issues.append(Issue(
            code="DISTINCT_USED",
            severity="info",
            message="DISTINCT can be expensive; if used to fix duplicates from joins, consider correcting join conditions instead.",
        ))

    # Rule 8: ORDER BY without LIMIT (could be expensive)
    if structure.get("has_order_by") and not structure.get("has_limit"):
        issues.append(Issue(
            code="ORDER_BY_NO_LIMIT",
            severity="info",
            message="ORDER BY without LIMIT may require sorting many rows; consider adding LIMIT if appropriate.",
        ))

    return issues
