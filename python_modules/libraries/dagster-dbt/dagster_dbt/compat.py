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
            # dbt's own StrEnum stringifies to the value; the default Enum.__str__ would give
            # "NodeStatus.Pass", which silently diverges anywhere a status is formatted or
            # used as the value of another enum member.
            def __str__(self) -> str:
                return self.value

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
            Reused = "reused"

        class TestStatus(StrEnum):
            Pass = "pass"
            Error = "error"
            Fail = "fail"
            Warn = "warn"
            Skipped = "skipped"


logging.getLogger().handlers = existing_root_logger_handlers


# The statuses a refable node (model, seed, snapshot) can end on without having failed.
# Anything outside this set yields no materialization.
#
# Use this ONLY for refable nodes -- it is not valid for tests. `warn` is a success for a
# refable node but a warn-severity failure for a test, and the two are indistinguishable on
# the wire, so the test path must keep comparing against `TestStatus`.
#
# - `no-op` (dbt-core 1.10+) and `reused` (dbt-core 1.12+, and every `Reused*` variant in dbt
#   Fusion) are terminal, non-error statuses meaning dbt deliberately did not rebuild the node.
#   The relation still exists in the warehouse, so an event must be emitted or the asset
#   silently stops updating.
# `partial success` is deliberately absent: dbt lists it in `MARK_DEPENDENT_ERRORS_STATUSES`,
# so dbt itself marks the node's dependents as errored and the step fails. Materializing it
# would show the asset healthy on a partial load and let downstream automation run on it.
# - `warn` is what dbt Fusion serializes `SucceededWithWarning` to: the node built but emitted
#   a warning (e.g. duplicate columns). Fusion maps that status to a successful outcome, and
#   dbt-core's `RunStatus` has no `warn` member at all, so accepting it cannot mask a dbt-core
#   failure.
#
# Spelled as string literals because none of these is a `NodeStatus` member across the whole
# dbt-core range this package supports.
SUCCESSFUL_NODE_STATUSES: frozenset[str] = frozenset(
    {
        "success",
        "no-op",
        "reused",
        "warn",
    }
)
