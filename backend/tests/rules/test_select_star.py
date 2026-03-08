"""Tests for SelectStarRule"""

import pytest
from app.rules.select_star import SelectStarRule


class TestSelectStarRule:
    """Tests for SELECT * detection"""

    @pytest.fixture
    def rule(self):
        return SelectStarRule()

    # ===================
    # Should trigger
    # ===================

    def test_simple_select_star(self, parse, rule):
        """Basic SELECT * should trigger"""
        tree = parse("SELECT * FROM users")
        issues = rule.check("SELECT * FROM users", tree, "postgres")
        assert len(issues) == 1
        assert issues[0].code == "SELECT_STAR"
        assert issues[0].severity == "warning"

    def test_select_star_with_where(self, parse, rule):
        """SELECT * with WHERE clause should still trigger"""
        sql = "SELECT * FROM users WHERE active = true"
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 1
        assert issues[0].code == "SELECT_STAR"

    def test_select_star_with_join(self, parse, rule):
        """SELECT * with JOIN should trigger"""
        sql = "SELECT * FROM users u JOIN orders o ON u.id = o.user_id"
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 1
        assert issues[0].code == "SELECT_STAR"

    def test_select_star_with_table_alias(self, parse, rule):
        """SELECT t.* should trigger"""
        sql = "SELECT u.* FROM users u"
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 1
        assert issues[0].code == "SELECT_STAR"

    def test_select_star_in_subquery(self, parse, rule):
        """SELECT * in subquery should trigger"""
        sql = "SELECT id FROM (SELECT * FROM users) sub"
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 1
        assert issues[0].code == "SELECT_STAR"

    def test_select_star_in_cte(self, parse, rule):
        """SELECT * in CTE should trigger"""
        sql = "WITH cte AS (SELECT * FROM users) SELECT id FROM cte"
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 1
        assert issues[0].code == "SELECT_STAR"

    def test_select_star_with_order_by(self, parse, rule):
        """SELECT * with ORDER BY should trigger"""
        sql = "SELECT * FROM users ORDER BY created_at DESC"
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 1
        assert issues[0].code == "SELECT_STAR"

    def test_select_star_with_limit(self, parse, rule):
        """SELECT * with LIMIT should still trigger"""
        sql = "SELECT * FROM users LIMIT 10"
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 1
        assert issues[0].code == "SELECT_STAR"

    # ===================
    # Should NOT trigger
    # ===================

    def test_explicit_columns_no_issue(self, parse, rule):
        """Explicit column selection should not trigger"""
        sql = "SELECT id, name, email FROM users"
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 0

    def test_single_column_no_issue(self, parse, rule):
        """Single column selection should not trigger"""
        sql = "SELECT id FROM users"
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 0

    def test_count_star_no_issue(self, parse, rule):
        """COUNT(*) should not trigger SELECT_STAR rule"""
        sql = "SELECT COUNT(*) FROM users"
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 0

    def test_aggregate_with_columns_no_issue(self, parse, rule):
        """Aggregate query with explicit columns should not trigger"""
        sql = "SELECT user_id, SUM(amount) FROM orders GROUP BY user_id"
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 0

    def test_aliased_columns_no_issue(self, parse, rule):
        """Aliased columns should not trigger"""
        sql = "SELECT id AS user_id, name AS user_name FROM users"
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 0

    def test_expression_columns_no_issue(self, parse, rule):
        """Expression columns should not trigger"""
        sql = "SELECT UPPER(name), CONCAT(first_name, ' ', last_name) FROM users"
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 0

    # ===================
    # Dialect variations
    # ===================

    def test_mysql_select_star(self, parse, rule):
        """MySQL SELECT * should trigger"""
        sql = "SELECT * FROM users"
        tree = parse(sql, dialect="mysql")
        issues = rule.check(sql, tree, "mysql")
        assert len(issues) == 1
        assert issues[0].code == "SELECT_STAR"

    def test_sqlite_select_star(self, parse, rule):
        """SQLite SELECT * should trigger"""
        sql = "SELECT * FROM users"
        tree = parse(sql, dialect="sqlite")
        issues = rule.check(sql, tree, "sqlite")
        assert len(issues) == 1
        assert issues[0].code == "SELECT_STAR"

    def test_tsql_select_star(self, parse, rule):
        """SQL Server (TSQL) SELECT * should trigger"""
        sql = "SELECT * FROM users"
        tree = parse(sql, dialect="tsql")
        issues = rule.check(sql, tree, "tsql")
        assert len(issues) == 1
        assert issues[0].code == "SELECT_STAR"

    def test_bigquery_select_star(self, parse, rule):
        """BigQuery SELECT * should trigger"""
        sql = "SELECT * FROM users"
        tree = parse(sql, dialect="bigquery")
        issues = rule.check(sql, tree, "bigquery")
        assert len(issues) == 1
        assert issues[0].code == "SELECT_STAR"

    def test_snowflake_select_star(self, parse, rule):
        """Snowflake SELECT * should trigger"""
        sql = "SELECT * FROM users"
        tree = parse(sql, dialect="snowflake")
        issues = rule.check(sql, tree, "snowflake")
        assert len(issues) == 1
        assert issues[0].code == "SELECT_STAR"

    # ===================
    # Evidence check
    # ===================

    def test_evidence_contains_select_star(self, parse, rule):
        """Evidence should show SELECT *"""
        sql = "SELECT * FROM users"
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 1
        assert "SELECT *" in issues[0].evidence
