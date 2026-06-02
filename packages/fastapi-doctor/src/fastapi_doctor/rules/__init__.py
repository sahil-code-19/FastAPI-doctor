# Import all rule modules here to trigger @register_rule decorator
from .async_sync import DbSessionInAsyncRule, SyncBlockingIORule
from .correctness import MissingStatusCodeRule
from .security import (
    MissingResponseModelRule,
    ResponseModelNoneRule,
    ReturnSqlalchemyBaseClass,
)

__all__ = [
    "DbSessionInAsyncRule",
    "MissingResponseModelRule",
    "MissingStatusCodeRule",
    "ResponseModelNoneRule",
    "ReturnSqlalchemyBaseClass",
    "SyncBlockingIORule",
]
