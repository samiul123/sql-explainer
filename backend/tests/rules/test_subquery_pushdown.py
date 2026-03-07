"""Tests for SubqueryPushdownRule"""

import pytest
from app.rules.subquery_pushdown import (
    SubqueryPushdownRule,
    get_computed_columns,
    get_aggregate_columns,
    get_inner_filter_predicates,
)


class TestGetComputedColumns:
    """Tests for get_computed_columns helper"""

    def test_simple_columns_not_computed(self, parse):
        tree = parse("SELECT user_id, name FROM users")
        computed = get_computed_columns(tree)
        assert "user_id" not in computed
        assert "name" not in computed

    def test_aliased_expression_is_computed(self, parse):
        tree = parse("SELECT user_id, UPPER(name) AS upper_name FROM users")
        computed = get_computed_columns(tree)
        assert "upper_name" in computed

    def test_arithmetic_expression_is_computed(self, parse):
        tree = parse("SELECT price * quantity AS total FROM orders")
        computed = get_computed_columns(tree)
        assert "total" in computed


class TestGetAggregateColumns:
    """Tests for get_aggregate_columns helper"""

    def test_count_is_aggregate(self, parse):
        tree = parse("SELECT user_id, COUNT(*) AS cnt FROM orders GROUP BY user_id")
        aggregates = get_aggregate_columns(tree)
        assert "cnt" in aggregates

    def test_sum_is_aggregate(self, parse):
        tree = parse("SELECT user_id, SUM(amount) AS total FROM orders GROUP BY user_id")
        aggregates = get_aggregate_columns(tree)
        assert "total" in aggregates

    def test_non_aggregate_not_included(self, parse):
        tree = parse("SELECT user_id, SUM(amount) AS total FROM orders GROUP BY user_id")
        aggregates = get_aggregate_columns(tree)
        assert "user_id" not in aggregates


class TestGetInnerFilterPredicates:
    """Tests for get_inner_filter_predicates helper"""

    def test_extracts_equality_filter(self, parse):
        tree = parse("SELECT * FROM orders WHERE status = 'completed'")
        where = tree.args.get("where")
        predicates = get_inner_filter_predicates(where)
        assert "status" in predicates

    def test_extracts_multiple_filters(self, parse):
        tree = parse("SELECT * FROM orders WHERE status = 'done' AND user_id = 100")
        where = tree.args.get("where")
        predicates = get_inner_filter_predicates(where)
        assert "status" in predicates
        assert "user_id" in predicates

    def test_returns_empty_for_no_where(self, parse):
        predicates = get_inner_filter_predicates(None)
        assert predicates == {}


class TestSubqueryPushdownRule:
    """Tests for the main SubqueryPushdownRule"""

    @pytest.fixture
    def rule(self):
        return SubqueryPushdownRule()

    # ==================== Subquery Tests ====================

    def test_detects_pushable_filter_on_subquery(self, rule, parse):
        """Should detect filter that can be pushed into subquery"""
        # ❌ Bad: Filter applied AFTER subquery materializes all rows
        sql = """
            SELECT * FROM (
                SELECT user_id, SUM(amount) AS total
                FROM orders
                GROUP BY user_id
            ) sub
            WHERE sub.user_id = 100
        """
        # ✅ Good: Filter pushed INTO subquery, reduces rows before aggregation
        # SELECT * FROM (
        #     SELECT user_id, SUM(amount) AS total
        #     FROM orders
        #     WHERE user_id = 100
        #     GROUP BY user_id
        # ) sub
        
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        
        assert len(issues) == 1
        assert issues[0].code == "SUBQUERY_PUSHDOWN_OPPORTUNITY"
        assert "user_id" in issues[0].message

    def test_skips_aggregate_column_filter(self, rule, parse):
        """Should NOT flag filter on aggregate column (can't push)"""
        # This is correct - can't push filter on 'total' because it's computed by SUM()
        sql = """
            SELECT * FROM (
                SELECT user_id, SUM(amount) AS total
                FROM orders
                GROUP BY user_id
            ) sub
            WHERE sub.total > 1000
        """
        # No optimization possible - 'total' doesn't exist until after aggregation
        
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        
        pushdown_issues = [i for i in issues if "PUSHDOWN" in i.code]
        assert len(pushdown_issues) == 0

    def test_skips_computed_column_filter(self, rule, parse):
        """Should NOT flag filter on computed column"""
        # This is correct - can't push filter on 'upper_name' because it's computed
        sql = """
            SELECT * FROM (
                SELECT user_id, UPPER(name) AS upper_name
                FROM users
            ) sub
            WHERE sub.upper_name = 'JOHN'
        """
        # ✅ Alternative: Push the equivalent filter inside
        # SELECT * FROM (
        #     SELECT user_id, UPPER(name) AS upper_name
        #     FROM users
        #     WHERE UPPER(name) = 'JOHN'
        # ) sub
        # (But that's a different optimization - requires expression matching)
        
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        
        pushdown_issues = [i for i in issues if "PUSHDOWN" in i.code]
        assert len(pushdown_issues) == 0

    def test_detects_additional_pushable_filters(self, rule, parse):
        """Should detect filters that can be pushed even when subquery has some filters"""
        # ❌ Bad: Subquery has partial filter, but more filters could be pushed
        sql = """
            SELECT * FROM (
                SELECT * FROM orders WHERE status = 'completed'
            ) sub
            WHERE sub.user_id = 100 AND sub.created_at > '2024-01-01'
        """
        # ✅ Good: All filters pushed into subquery
        # SELECT * FROM (
        #     SELECT * FROM orders
        #     WHERE status = 'completed'
        #       AND user_id = 100
        #       AND created_at > '2024-01-01'
        # ) sub
        
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        
        pushdown_issues = [i for i in issues if "PUSHDOWN" in i.code]
        assert len(pushdown_issues) == 2

    def test_skips_duplicate_filter(self, rule, parse):
        """Should NOT flag filter that already exists inside subquery"""
        # This is fine (though redundant) - filter already exists inside
        sql = """
            SELECT * FROM (
                SELECT * FROM orders WHERE user_id = 100
            ) sub
            WHERE sub.user_id = 100
        """
        # ✅ Good: Just remove the redundant outer filter
        # SELECT * FROM (
        #     SELECT * FROM orders WHERE user_id = 100
        # ) sub
        
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        
        pushdown_issues = [i for i in issues if "PUSHDOWN" in i.code]
        assert len(pushdown_issues) == 0

    def test_no_issue_without_outer_where(self, rule, parse):
        """Should return no issues when there's no outer WHERE"""
        # No optimization needed - no outer filter to push
        sql = """
            SELECT * FROM (
                SELECT user_id, SUM(amount) AS total
                FROM orders
                GROUP BY user_id
            ) sub
        """
        
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        
        assert len(issues) == 0

    def test_no_issue_without_subquery(self, rule, parse):
        """Should return no issues for simple query without subquery"""
        # Simple query - no subquery to push into
        sql = "SELECT * FROM orders WHERE user_id = 100"
        
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        
        pushdown_issues = [i for i in issues if "PUSHDOWN" in i.code]
        assert len(pushdown_issues) == 0

    # ==================== CTE Tests ====================

    def test_detects_pushable_filter_on_cte(self, rule, parse):
        """Should detect filter that can be pushed into CTE"""
        # ❌ Bad: CTE processes ALL users, then outer query filters
        sql = """
            WITH order_totals AS (
                SELECT user_id, SUM(amount) AS total
                FROM orders
                GROUP BY user_id
            )
            SELECT * FROM order_totals WHERE user_id = 100
        """
        # ✅ Good: Filter pushed into CTE
        # WITH order_totals AS (
        #     SELECT user_id, SUM(amount) AS total
        #     FROM orders
        #     WHERE user_id = 100
        #     GROUP BY user_id
        # )
        # SELECT * FROM order_totals
        
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        
        cte_issues = [i for i in issues if i.code == "CTE_PUSHDOWN_OPPORTUNITY"]
        assert len(cte_issues) == 1
        assert "user_id" in cte_issues[0].message

    def test_skips_aggregate_column_filter_on_cte(self, rule, parse):
        """Should NOT flag filter on CTE aggregate column"""
        # This is correct - can't push filter on 'total' into CTE
        sql = """
            WITH order_totals AS (
                SELECT user_id, SUM(amount) AS total
                FROM orders
                GROUP BY user_id
            )
            SELECT * FROM order_totals WHERE total > 1000
        """
        # No optimization possible - must compute all totals first
        
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        
        cte_issues = [i for i in issues if "CTE_PUSHDOWN" in i.code]
        assert len(cte_issues) == 0

    # ==================== Edge Cases ====================

    def test_like_filter_detection(self, rule, parse):
        """Should detect LIKE filters as pushable"""
        # ❌ Bad: LIKE filter outside subquery
        sql = """
            SELECT * FROM (SELECT * FROM users) sub
            WHERE sub.name LIKE 'John%'
        """
        # ✅ Good: LIKE filter inside subquery
        # SELECT * FROM (
        #     SELECT * FROM users WHERE name LIKE 'John%'
        # ) sub
        
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        
        pushdown_issues = [i for i in issues if "PUSHDOWN" in i.code]
        assert len(pushdown_issues) == 1

    def test_in_clause_filter_detection(self, rule, parse):
        """Should detect IN clause filters as pushable"""
        # ❌ Bad: IN filter outside subquery
        sql = """
            SELECT * FROM (SELECT * FROM orders) sub
            WHERE sub.status IN ('completed', 'shipped')
        """
        # ✅ Good: IN filter inside subquery
        # SELECT * FROM (
        #     SELECT * FROM orders WHERE status IN ('completed', 'shipped')
        # ) sub
        
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        
        pushdown_issues = [i for i in issues if "PUSHDOWN" in i.code]
        assert len(pushdown_issues) == 1

    def test_between_filter_detection(self, rule, parse):
        """Should detect BETWEEN filters as pushable"""
        # ❌ Bad: BETWEEN filter outside subquery
        sql = """
            SELECT * FROM (SELECT * FROM orders) sub
            WHERE sub.amount BETWEEN 100 AND 500
        """
        # ✅ Good: BETWEEN filter inside subquery
        # SELECT * FROM (
        #     SELECT * FROM orders WHERE amount BETWEEN 100 AND 500
        # ) sub
        
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        
        pushdown_issues = [i for i in issues if "PUSHDOWN" in i.code]
        assert len(pushdown_issues) == 1

    def test_date_range_filter_on_computed(self, rule, parse):
        """Should NOT flag date filter on computed column"""
        # This is correct - can't push filter on 'order_date' (computed)
        sql = """
            SELECT * FROM (
                SELECT DATE(created_at) as order_date, COUNT(*) as cnt
                FROM orders
                GROUP BY DATE(created_at)
            ) sub
            WHERE sub.order_date >= '2024-01-01'
        """
        # ✅ Good: Push equivalent filter on source column
        # SELECT * FROM (
        #     SELECT DATE(created_at) as order_date, COUNT(*) as cnt
        #     FROM orders
        #     WHERE created_at >= '2024-01-01'
        #     GROUP BY DATE(created_at)
        # ) sub
        # Note: Requires manual rewrite to filter on 'created_at' instead
        
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        
        # Should NOT flag because 'order_date' is computed
        pushdown_issues = [i for i in issues if "PUSHDOWN" in i.code]
        assert len(pushdown_issues) == 0

    def test_join_with_subquery(self, rule, parse):
        """Should detect filters pushable into joined subquery"""
        # ❌ Bad: Subquery returns ALL users
        sql = """
            SELECT u.name, s.total_orders
            FROM users u
            JOIN (
                SELECT user_id, COUNT(*) as total_orders
                FROM orders
                GROUP BY user_id
            ) s ON u.id = s.user_id
            WHERE s.user_id = 100
        """
        # ✅ Good: Filter pushed into subquery
        # SELECT u.name, s.total_orders
        # FROM users u
        # JOIN (
        #     SELECT user_id, COUNT(*) as total_orders
        #     FROM orders
        #     WHERE user_id = 100
        #     GROUP BY user_id
        # ) s ON u.id = s.user_id
        
        tree = parse(sql)
        issues = rule.check(sql, tree, "postgres")
        
        pushdown_issues = [i for i in issues if "PUSHDOWN" in i.code]
        assert len(pushdown_issues) == 1


class TestIntegrationWithLinter:
    """Integration tests using the full linter"""

    def test_rule_is_registered(self, linter):
        lint = linter("postgres")
        rule_types = [type(r).__name__ for r in lint.rules]
        assert "SubqueryPushdownRule" in rule_types

    def test_full_analysis_flow(self, linter):
        # ❌ Bad: Filter after subquery
        sql = """
            SELECT * FROM (
                SELECT user_id, SUM(amount) AS total
                FROM orders
                GROUP BY user_id
            ) sub
            WHERE sub.user_id = 100
        """
        # ✅ Good: Filter inside subquery
        # SELECT * FROM (
        #     SELECT user_id, SUM(amount) AS total
        #     FROM orders
        #     WHERE user_id = 100
        #     GROUP BY user_id
        # ) sub
        
        lint = linter("postgres")
        _, _, _, issues = lint.analyze(sql)
        
        pushdown_issues = [i for i in issues if "PUSHDOWN" in i.code]
        assert len(pushdown_issues) == 1
