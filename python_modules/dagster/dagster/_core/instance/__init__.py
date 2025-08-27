# Import and re-export commonly used symbols for backwards compatibility
from collections.abc import Mapping
from typing import Any

from typing_extensions import TypeAlias

from dagster._core.instance.instance import DagsterInstance as DagsterInstance
from dagster._core.instance.ref import InstanceRef as InstanceRef
from dagster._core.instance.types import (
    CachingDynamicPartitionsLoader as CachingDynamicPartitionsLoader,
    DynamicPartitionsStore as DynamicPartitionsStore,
    InstanceType as InstanceType,
    MayHaveInstanceWeakref as MayHaveInstanceWeakref,
    T_DagsterInstance as T_DagsterInstance,
)
from dagster._core.instance.utils import (
    RUNLESS_JOB_NAME as RUNLESS_JOB_NAME,
    RUNLESS_RUN_ID as RUNLESS_RUN_ID,
)

# Re-export for backward compatibility - internal repo depends on this export from instance module
from dagster._time import get_current_timestamp as get_current_timestamp

# Type alias for backward compatibility
DagsterInstanceOverrides: TypeAlias = Mapping[str, Any]

# Re-export for backward compatibility
__all__ = [
    "RUNLESS_JOB_NAME",
    "RUNLESS_RUN_ID",
    "DagsterInstance",
    "DagsterInstanceOverrides",
    "DynamicPartitionsStore",
    "InstanceRef",
    "InstanceType",
    "MayHaveInstanceWeakref",
    "T_DagsterInstance",
    "get_current_timestamp",
]
