# Import all rule modules here to trigger @register_rule decorator
from .async_sync import DbSessionInAsyncRule, SyncBlockingIORule
from .correctness import MissingStatusCodeRule

__all__ = [
    "DbSessionInAsyncRule",
    "MissingStatusCodeRule",
    "SyncBlockingIORule",
]
