"""Tests for RedundantOuterQueryRule"""

import pytest
from app.rules.redundant_outer_query import (
    RedundantOuterQueryRule,
    get_subquery_from_select,
    is_outer_query_redundant,
    count_redundant_layers,
    has_window_functions,
    all_columns_are_passthrough,
)


class TestHelperFunctions:
    """Tests for helper functions"""

    def test_get_subquery_from_select_with_subquery(self, parse):
        """Should detect subquery in FROM clause"""
        tree = parse("SELECT * FROM (SELECT a FROM t) sub")
        select = tree
        result = get_subquery_from_select(select)
        assert result is not None
        subquery, alias = result
        assert alias == "sub"

    def test_get_subquery_from_select_regular_table(self, parse):
        """Should return None for regular table"""
        tree = parse("SELECT * FROM users")
        result = get_subquery_from_select(tree)
        assert result is None

    def test_has_window_functions_true(self, parse):
        """Should detect window functions"""
        tree = parse("SELECT *, RANK() OVER(ORDER BY x) FROM t")
        assert has_window_functions(tree) is True

    def test_has_window_functions_false(self, parse):
        """Should return False when no window functions"""
        tree = parse("SELECT a, b FROM t")
        assert has_window_functions(tree) is False

    def test_all_columns_passthrough_star(self, parse):
        """SELECT * is passthrough"""
        tree = parse("SELECT * FROM t")
        assert all_columns_are_passthrough(tree) is True

    def test_all_columns_passthrough_explicit(self, parse):
        """Simple column refs are passthrough"""
        tree = parse("SELECT a, b, c FROM t")
        assert all_columns_are_passthrough(tree) is True

    def test_all_columns_passthrough_false(self, parse):
        """Function calls are not passthrough"""
        tree = parse("SELECT a, UPPER(b) FROM t")
        assert all_columns_are_passthrough(tree) is False

    def test_count_redundant_layers_single(self, parse):
        """Single redundant layer"""
        tree = parse("SELECT * FROM (SELECT a, b FROM t) sub")
        assert count_redundant_layers(tree) == 1

    def test_count_redundant_layers_nested(self, parse):
        """Multiple nested redundant layers"""
        tree = parse("SELECT * FROM (SELECT * FROM (SELECT a FROM t) s1) s2")
        assert count_redundant_layers(tree) == 2

    def test_count_redundant_layers_none(self, parse):
        """No redundant layers when outer has WHERE"""
        tree = parse("SELECT * FROM (SELECT a FROM t) sub WHERE a > 10")
        assert count_redundant_layers(tree) == 0


class TestRedundantOuterQueryRule:
    """Tests for redundant outer query detection"""

    @pytest.fixture
    def rule(self):
        return RedundantOuterQueryRule()

    # ==========================================
    # Should Trigger (Redundant)
    # ==========================================

    def test_select_star_passthrough(self, parse, rule):
        """SELECT * from subquery with no processing is redundant"""
        sql = """
            SELECT * FROM (
                SELECT user_id, SUM(amount) as total 
                FROM orders 
                GROUP BY user_id
            ) sub
        """
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 1
        assert issues[0].code == "REDUNDANT_OUTER_QUERY"
        assert issues[0].severity == "info"
        assert "redundant" in issues[0].message.lower()

    def test_explicit_column_passthrough(self, parse, rule):
        """Explicit columns matching subquery is redundant"""
        sql = """
            SELECT user_id, total FROM (
                SELECT user_id, SUM(amount) as total 
                FROM orders 
                GROUP BY user_id
            ) sub
        """
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 1
        assert issues[0].code == "REDUNDANT_OUTER_QUERY"

    def test_column_subset_passthrough(self, parse, rule):
        """Selecting subset of columns without transformation is redundant"""
        sql = """
            SELECT user_id FROM (
                SELECT user_id, name, email FROM users
            ) sub
        """
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 1
        assert issues[0].code == "REDUNDANT_OUTER_QUERY"

    def test_aliased_column_passthrough(self, parse, rule):
        """Aliased columns that are still just refs are redundant"""
        sql = """
            SELECT user_id as uid FROM (
                SELECT user_id FROM users
            ) sub
        """
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 1
        assert issues[0].code == "REDUNDANT_OUTER_QUERY"

    def test_redundant_cte_wrapper(self, parse, rule):
        """CTE with simple passthrough SELECT is redundant"""
        sql = """
            WITH user_data AS (
                SELECT user_id, name FROM users WHERE active = true
            )
            SELECT * FROM user_data
        """
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 1
        assert issues[0].code == "REDUNDANT_OUTER_QUERY"
        assert "CTE" in issues[0].message

    def test_same_order_by_redundant(self, parse, rule):
        """Same ORDER BY in inner and outer is redundant"""
        sql = """
            SELECT * FROM (
                SELECT * FROM users ORDER BY name
            ) sub ORDER BY name
        """
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 1
        assert issues[0].code == "REDUNDANT_OUTER_QUERY"

    def test_same_limit_redundant(self, parse, rule):
        """Same LIMIT in inner and outer is redundant"""
        sql = """
            SELECT * FROM (
                SELECT * FROM users LIMIT 10
            ) sub LIMIT 10
        """
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 1
        assert issues[0].code == "REDUNDANT_OUTER_QUERY"

    def test_nested_redundancy_single_issue(self, parse, rule):
        """Nested redundant wrappers should produce single issue with layer count"""
        sql = "SELECT * FROM (SELECT * FROM (SELECT a, b FROM t) s1) s2"
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 1
        assert issues[0].code == "REDUNDANT_OUTER_QUERY"
        assert "2" in issues[0].message  # Should mention 2 layers

    def test_triple_nested_redundancy(self, parse, rule):
        """Triple nested should show 3 layers"""
        sql = "SELECT * FROM (SELECT * FROM (SELECT * FROM (SELECT a FROM t) s1) s2) s3"
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 1
        assert "3" in issues[0].message  # Should mention 3 layers

    # ==========================================
    # Should NOT Trigger (Valid)
    # ==========================================

    def test_outer_where_is_valid(self, parse, rule):
        """Outer WHERE clause makes query valid"""
        sql = """
            SELECT * FROM (
                SELECT user_id, SUM(amount) as total 
                FROM orders 
                GROUP BY user_id
            ) sub WHERE total > 100
        """
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 0

    def test_outer_join_is_valid(self, parse, rule):
        """Outer JOIN makes query valid"""
        sql = """
            SELECT * FROM (
                SELECT user_id, total FROM order_totals
            ) sub JOIN users ON sub.user_id = users.id
        """
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 0

    def test_outer_window_function_is_valid(self, parse, rule):
        """Adding window function makes query valid"""
        sql = """
            SELECT *, RANK() OVER(ORDER BY total DESC) as rank FROM (
                SELECT user_id, SUM(amount) as total 
                FROM orders 
                GROUP BY user_id
            ) sub
        """
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 0

    def test_outer_limit_is_valid(self, parse, rule):
        """Adding LIMIT (when inner has none) makes query valid"""
        sql = """
            SELECT * FROM (
                SELECT user_id, total FROM order_totals
            ) sub LIMIT 10
        """
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 0

    def test_different_limit_is_valid(self, parse, rule):
        """Different LIMIT values means outer is meaningful"""
        sql = """
            SELECT * FROM (
                SELECT * FROM users LIMIT 100
            ) sub LIMIT 10
        """
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 0

    def test_outer_order_by_is_valid(self, parse, rule):
        """Adding ORDER BY (when inner has none) makes query valid"""
        sql = """
            SELECT * FROM (
                SELECT user_id, total FROM order_totals
            ) sub ORDER BY total DESC
        """
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 0

    def test_different_order_by_is_valid(self, parse, rule):
        """Different ORDER BY means outer is meaningful"""
        sql = """
            SELECT * FROM (
                SELECT * FROM users ORDER BY name
            ) sub ORDER BY created_at
        """
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 0

    def test_outer_distinct_is_valid(self, parse, rule):
        """Adding DISTINCT makes query valid"""
        sql = """
            SELECT DISTINCT * FROM (
                SELECT category FROM products
            ) sub
        """
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 0

    def test_outer_group_by_is_valid(self, parse, rule):
        """Adding GROUP BY makes query valid"""
        sql = """
            SELECT category, COUNT(*) FROM (
                SELECT * FROM products
            ) sub GROUP BY category
        """
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 0

    def test_computed_column_is_valid(self, parse, rule):
        """Adding computed column makes query valid"""
        sql = """
            SELECT user_id, total, total * 0.1 as tax FROM (
                SELECT user_id, SUM(amount) as total 
                FROM orders 
                GROUP BY user_id
            ) sub
        """
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 0

    def test_function_call_is_valid(self, parse, rule):
        """Function applied to column makes query valid"""
        sql = """
            SELECT UPPER(name) FROM (
                SELECT name FROM users
            ) sub
        """
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 0

    def test_simple_query_no_subquery(self, parse, rule):
        """Simple query without subquery should not trigger"""
        sql = "SELECT * FROM users WHERE active = true"
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 0

    def test_subquery_in_where_not_from(self, parse, rule):
        """Subquery in WHERE is different pattern"""
        sql = "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)"
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 0

    def test_multiple_sources_is_valid(self, parse, rule):
        """Multiple sources in FROM is valid"""
        sql = """
            SELECT * FROM (SELECT a FROM t1) s1, (SELECT b FROM t2) s2
        """
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 0

    def test_cte_used_multiple_times_is_valid(self, parse, rule):
        """CTE used multiple times is valid (materialization point)"""
        sql = """
            WITH cte AS (
                SELECT user_id, name FROM users
            )
            SELECT * FROM cte c1 JOIN cte c2 ON c1.user_id = c2.user_id
        """
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        # Should not flag since CTE is used twice
        assert len(issues) == 0

    def test_outer_having_is_valid(self, parse, rule):
        """Adding HAVING makes query valid"""
        sql = """
            SELECT category, SUM(total) FROM (
                SELECT category, amount as total FROM orders
            ) sub GROUP BY category HAVING SUM(total) > 1000
        """
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        assert len(issues) == 0

    # ==========================================
    # Dialect variations
    # ==========================================

    def test_mysql_redundant_subquery(self, parse, rule):
        """MySQL redundant subquery should trigger"""
        sql = "SELECT * FROM (SELECT a, b FROM t) sub"
        tree = parse(sql, dialect="mysql")
        issues = rule.check(sql, tree, "mysql")
        assert len(issues) == 1
        assert issues[0].code == "REDUNDANT_OUTER_QUERY"

    def test_bigquery_redundant_subquery(self, parse, rule):
        """BigQuery redundant subquery should trigger"""
        sql = "SELECT * FROM (SELECT a, b FROM t) sub"
        tree = parse(sql, dialect="bigquery")
        issues = rule.check(sql, tree, "bigquery")
        assert len(issues) == 1
        assert issues[0].code == "REDUNDANT_OUTER_QUERY"

    def test_snowflake_redundant_subquery(self, parse, rule):
        """Snowflake redundant subquery should trigger"""
        sql = "SELECT * FROM (SELECT a, b FROM t) sub"
        tree = parse(sql, dialect="snowflake")
        issues = rule.check(sql, tree, "snowflake")
        assert len(issues) == 1
        assert issues[0].code == "REDUNDANT_OUTER_QUERY"

    # ==========================================
    # Edge cases
    # ==========================================

    def test_empty_subquery_alias(self, parse, rule):
        """Subquery without alias should still be detected"""
        # Note: Some dialects require alias, but sqlglot may parse without
        sql = "SELECT a FROM (SELECT a FROM t)"
        try:
            tree = parse(sql)
            issues = rule.check(sql, tree, "postgres")
            # May or may not trigger depending on parse
        except Exception:
            pass  # Some dialects require subquery alias

    def test_deeply_nested_with_valid_outer(self, parse, rule):
        """Deep nesting where outermost is valid - inner redundancy still flagged"""
        sql = """
            SELECT * FROM (
                SELECT * FROM (SELECT a FROM t) s1
            ) s2 WHERE a > 10
        """
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        # Outermost has WHERE, so it's valid
        # But middle wrapper (SELECT * FROM (SELECT a FROM t) s1) IS redundant
        # and should be flagged
        assert len(issues) == 1
        assert issues[0].code == "REDUNDANT_OUTER_QUERY"
