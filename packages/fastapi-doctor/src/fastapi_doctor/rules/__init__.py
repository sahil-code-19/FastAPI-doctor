# Import all rule modules here to trigger @register_rule decorator
from .architecture import (
    DependsInBodyRule,
    DeprecatedOnEventRule,
    FileInsteadOfUploadFileRule,
    GlobalMutableStateRule,
    GodFilePatternRule,
    RawDbConnectStartupRule,
    UnusedRequestParamRule,
)
from .async_sync import DbSessionInAsyncRule, SyncBlockingIORule
from .correctness import MissingStatusCodeRule
from .dependency import (
    GetDbWithoutTryFinallyRule,
    RepeatedDependsRule,
    RouteLevelAuthRule,
    SessionWithoutYieldRule,
)
from .performance import (
    BackgroundTasksCeleryRule,
    CpuBoundInAsyncRule,
    MissingJoinedloadRule,
    MissingLruCacheRule,
    NPlusOneQueryRule,
    UnindexedForeignKeyRule,
)
from .pydantic import (
    DictInsteadOfModelDumpRule,
    MissingFromAttributesRule,
    OrmModeUnusedRule,
    PydanticV1ValidatorRule,
    RawDictWithResponseModelRule,
)
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
    "BackgroundTasksCeleryRule",
    "CorsWildcardCredentialsRule",
    "CpuBoundInAsyncRule",
    "DbSessionInAsyncRule",
    "DebugTrueNonTestFile",
    "DependsInBodyRule",
    "DeprecatedOnEventRule",
    "DictInsteadOfModelDumpRule",
    "FileInsteadOfUploadFileRule",
    "GetDbWithoutTryFinallyRule",
    "GlobalMutableStateRule",
    "GodFilePatternRule",
    "HardcodedSecretsRule",
    "MissingFromAttributesRule",
    "MissingHttpsRedirectMiddleware",
    "MissingJoinedloadRule",
    "MissingLruCacheRule",
    "MissingResponseModelRule",
    "MissingStatusCodeRule",
    "NPlusOneQueryRule",
    "OrmModeUnusedRule",
    "PydanticV1ValidatorRule",
    "RawDbConnectStartupRule",
    "RawDictWithResponseModelRule",
    "RepeatedDependsRule",
    "ResponseModelNoneRule",
    "ReturnSqlalchemyBaseClass",
    "RouteLevelAuthRule",
    "SessionWithoutYieldRule",
    "SqlFStringInjectionRule",
    "SyncBlockingIORule",
    "UnindexedForeignKeyRule",
    "UnusedRequestParamRule",
]
