# Import all rule modules here to trigger @register_rule decorator
from .async_sync import DbSessionInAsyncRule, SyncBlockingIORule
from .correctness import MissingStatusCodeRule
from .security import (
    CorsWildcardCredentialsRule,
    DebugTrueNonTestFile,
    HardcodedSecretsRule,
    MissingHttpsRedirectMiddleware,
    MissingResponseModelRule,
    ResponseModelNoneRule,
    ReturnSqlalchemyBaseClass,
    SqlFStringInjectionRule,
)

__all__ = [
    "CorsWildcardCredentialsRule",
    "DbSessionInAsyncRule",
    "DebugTrueNonTestFile",
    "HardcodedSecretsRule",
    "MissingHttpsRedirectMiddleware",
    "MissingResponseModelRule",
    "MissingStatusCodeRule",
    "ResponseModelNoneRule",
    "ReturnSqlalchemyBaseClass",
    "SqlFStringInjectionRule",
    "SyncBlockingIORule",
]
