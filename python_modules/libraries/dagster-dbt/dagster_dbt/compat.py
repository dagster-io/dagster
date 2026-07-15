import logging
from enum import Enum
from typing import TYPE_CHECKING, Any, TypeAlias

from packaging import version

# it's unclear exactly which dbt import adds a handler to the root logger, but something certainly does!
# on this line, we keep track of the set of handlers that are on the root logger BEFORE any dbt imports
# happen. at the end of this file, we set the root logger's handlers to the original set to ensure that
# after this file is loaded, the root logger's handlers will be unchanged.
existing_root_logger_handlers = [*logging.getLogger().handlers]


try:
    from dbt.version import __version__ as dbt_version

    DBT_PYTHON_VERSION = version.parse(dbt_version)
except ImportError:
    DBT_PYTHON_VERSION = None

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
    if DBT_PYTHON_VERSION is not None:
        from dbt.adapters.base.impl import (
            BaseAdapter as BaseAdapter,
            BaseColumn as BaseColumn,
            BaseRelation as BaseRelation,
        )
        from dbt.contracts.results import NodeStatus, TestStatus
        from dbt.node_types import NodeType as NodeType

        if DBT_PYTHON_VERSION < version.parse("1.8.0"):
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
            NoOp = "no-op"

        class TestStatus(StrEnum):
            Pass = NodeStatus.Pass
            Error = NodeStatus.Error
            Fail = NodeStatus.Fail
            Warn = NodeStatus.Warn
            Skipped = NodeStatus.Skipped


logging.getLogger().handlers = existing_root_logger_handlers


# Node statuses that should be treated as successful materializations for the
# purposes of yielding Dagster asset events. Any status outside this set is
# treated as an error / skip / other, and no materialization event is emitted.
#
# In particular:
#   - "no-op" (NodeStatus.NoOp on dbt-core >= 1.10) — dbt state-reuse: the node
#     was skipped because state said it was already up-to-date. Semantically
#     equivalent to a successful materialization; must yield an event.
#   - "partial success" (NodeStatus.PartialSuccess on dbt-core >= 1.9) —
#     incremental microbatch partial completion. Some batches succeeded; treat
#     as materialization.
#
# String literals are used deliberately rather than NodeStatus.<Member> to keep
# import-time safe across the supported dbt-core version range (1.7-1.11) — the
# NoOp and PartialSuccess enum members are only present in newer dbt-core
# versions, but dagster-dbt still needs to import cleanly on older ones.
_SUCCESS_EQUIVALENT_NODE_STATUSES: frozenset[str] = frozenset({
    "success",
    "no-op",
    "partial success",
})
