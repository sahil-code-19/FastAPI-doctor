# Import all rule modules here to trigger @register_rule decorator
from .async_sync import DbSessionInAsyncRule, SyncBlockingIORule
from .correctness import MissingStatusCodeRule
from .security import (
    CorsWildcardCredentialsRule,
    DebugTrueNonTestFile,
    HardcodedSecretsRule,
    MissingResponseModelRule,
    ResponseModelNoneRule,
    ReturnSqlalchemyBaseClass,
)

__all__ = [
    "CorsWildcardCredentialsRule",
    "DbSessionInAsyncRule",
    "DebugTrueNonTestFile",
    "HardcodedSecretsRule",
    "MissingResponseModelRule",
    "MissingStatusCodeRule",
    "ResponseModelNoneRule",
    "ReturnSqlalchemyBaseClass",
    "SyncBlockingIORule",
]
