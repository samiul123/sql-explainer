"""SQL linting rules"""

from .base import Rule
from .select_star import SelectStarRule
from .count_star import CountStarRule
from .no_limit import NoLimitRule
from .leading_wildcard_like import LeadingWildcardLikeRule
from .or_in_where import OrInWhereRule
from .function_in_where import FunctionInWhereRule
from .join_without_on import JoinWithoutOnRule
from .distinct_used import DistinctUsedRule
from .order_by_no_limit import OrderByNoLimitRule
from .having_to_where import HavingToWhereRule
from .function_blocks_pushdown import FunctionBlocksPushdownRule
from .outer_join_where_filter import OuterJoinWhereFilterRule
from .subquery_pushdown import SubqueryPushdownRule

__all__ = [
    "Rule",
    "SelectStarRule",
    "CountStarRule",
    "NoLimitRule",
    "LeadingWildcardLikeRule",
    "OrInWhereRule",
    "FunctionInWhereRule",
    "JoinWithoutOnRule",
    "DistinctUsedRule",
    "OrderByNoLimitRule",
    "HavingToWhereRule",
    "FunctionBlocksPushdownRule",
    "OuterJoinWhereFilterRule",
    "SubqueryPushdownRule",
]
