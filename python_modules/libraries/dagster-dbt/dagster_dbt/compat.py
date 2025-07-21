from enum import Enum
from functools import lru_cache
from typing import TYPE_CHECKING, Any

from dagster_shared.record import record
from packaging import version
from typing_extensions import TypeAlias


@record
class DbtVersion:
    """Base class for representing the currently-installed dbt version."""

    version: str

    @property
    def is_fusion(self) -> bool:
        return self.version.startswith("2.")

    @property
    def is_core(self) -> bool:
        return not self.is_fusion

    def less_than(self, other: str) -> bool:
        return version.parse(self.version) < version.parse(other)

    def to_string(self) -> str:
        if self.is_fusion:
            return "fusion"
        else:
            return self.version


@lru_cache
def _get_dbt_version() -> DbtVersion:
    try:
        from dbt.version import __version__ as dbt_version

        return DbtVersion(version=dbt_version)
    except ImportError:
        # for now, do not attempt to get a more-specific version
        return DbtVersion(version="2.0.0")


DBT_VERSION = _get_dbt_version()


# Conditionally define types for various types we use from the dbt-core package
if TYPE_CHECKING:
    from dbt.adapters.base.impl import (
        BaseAdapter as _BaseAdapter,
        BaseColumn as _BaseColumn,
        BaseRelation as _BaseRelation,
    )
    from dbt.contracts.results import (
        NodeStatus as _NodeStatus,
        TestStatus as _TestStatus,
    )
    from dbt.node_types import NodeType as _NodeType

    BaseAdapter: TypeAlias = _BaseAdapter
    BaseColumn: TypeAlias = _BaseColumn
    BaseRelation: TypeAlias = _BaseRelation
    NodeStatus: TypeAlias = _NodeStatus
    NodeType: TypeAlias = _NodeType
    TestStatus: TypeAlias = _TestStatus
    REFABLE_NODE_TYPES: list[str] = []
else:
    if DBT_VERSION.is_core:
        from dbt.adapters.base.impl import (
            BaseAdapter as BaseAdapter,
            BaseColumn as BaseColumn,
            BaseRelation as BaseRelation,
        )
        from dbt.contracts.results import NodeStatus, TestStatus
        from dbt.node_types import NodeType as NodeType

        if DBT_VERSION.less_than("1.8.0"):
            from dbt.node_types import NodeType

            REFABLE_NODE_TYPES = NodeType.refable()
        else:
            from dbt.node_types import REFABLE_NODE_TYPES as REFABLE_NODE_TYPES
    else:
        # here, we define implementations for types that will not be available if dbt-core is not
        # installed
        BaseAdapter = Any
        BaseColumn = Any
        BaseRelation = Any
        REFABLE_NODE_TYPES = ["model", "seed", "snapshot"]

        class StrEnum(str, Enum):
            def _generate_next_value_(name, *_):
                return name

        class NodeType(StrEnum):
            Model = "model"
            Analysis = "analysis"
            Test = "test"
            Snapshot = "snapshot"
            Operation = "operation"
            Seed = "seed"
            RPCCall = "rpc"
            SqlOperation = "sql_operation"
            Documentation = "doc"
            Source = "source"
            Macro = "macro"
            Exposure = "exposure"
            Metric = "metric"
            Group = "group"
            SavedQuery = "saved_query"
            SemanticModel = "semantic_model"
            Unit = "unit_test"
            Fixture = "fixture"

        class NodeStatus(StrEnum):
            Success = "success"
            Error = "error"
            Fail = "fail"
            Warn = "warn"
            Skipped = "skipped"
            PartialSuccess = "partial success"
            Pass = "pass"
            RuntimeErr = "runtime error"

        class TestStatus(StrEnum):
            Pass = NodeStatus.Pass
            Error = NodeStatus.Error
            Fail = NodeStatus.Fail
            Warn = NodeStatus.Warn
            Skipped = NodeStatus.Skipped
