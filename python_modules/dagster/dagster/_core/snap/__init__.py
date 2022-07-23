"""
This module contains serializable classes that contain all the meta information
in our definitions and type systems. The purpose is to be able to represent
user-defined code artifacts (e.g. Pipelines Solids) in a serializable format
so that they can be persisted and manipulated in remote processes.

This will have a number of uses, but the most immediately germane are:

1) Persist *historical* pipeline and repository structures. This
will enable, in the short term, for the user to be able to go to a historical
run and view the meta information at that point in time.
2) Access metadata about dagster artifiacts that are resident in an external
process or container. For example, dagit uses these classes load and represent
metadata from user repositories that reside in different processes.

There are a few varietals of classes:

1) Snapshots. These are chunks of metadata that end up being persisted for
historical purposes. Examples include the PipelineSnapshot and
the ExecutionPlanSnapshot.

2) Indexes. These are classes (not persistable) that build indexes over the
snapshot data for fast access.

3) "Active Data". These classes are serializable but not meant to be persisted.
For example we do not persist preset configuration blocks since config
can contain sensitive information. However this information needs to be
communicated between user repositories and host processes such as dagit.

"""

from dagster._config import (
    ConfigEnumValueSnap,
    ConfigFieldSnap,
    ConfigSchemaSnapshot,
    ConfigTypeSnap,
    snap_from_config_type,
    snap_from_field,
)

from .config_types import build_config_schema_snapshot
from .dagster_types import build_dagster_type_namespace_snapshot
from .dep_snapshot import DependencyStructureIndex, SolidInvocationSnap
from .execution_plan_snapshot import (
    ExecutionPlanSnapshot,
    ExecutionStepInputSnap,
    ExecutionStepOutputSnap,
    ExecutionStepSnap,
    create_execution_plan_snapshot_id,
    snapshot_from_execution_plan,
)
from .mode import LoggerDefSnap, ModeDefSnap, ResourceDefSnap
from .pipeline_snapshot import PipelineSnapshot, create_pipeline_snapshot_id
from .solid import CompositeSolidDefSnap, SolidDefSnap, build_composite_solid_def_snap
