from datetime import datetime
from enum import Enum
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Dict,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Union,
)

from typing_extensions import Self

import dagster._check as check
from dagster._annotations import PublicAttr, public
from dagster._core.definitions.events import AssetKey
from dagster._core.origin import JobPythonOrigin
from dagster._core.storage.tags import PARENT_RUN_ID_TAG, ROOT_RUN_ID_TAG
from dagster._core.utils import make_new_run_id
from dagster._serdes.serdes import (
    NamedTupleSerializer,
    whitelist_for_serdes,
)

from .tags import (
    BACKFILL_ID_TAG,
    REPOSITORY_LABEL_TAG,
    RESUME_RETRY_TAG,
    SCHEDULE_NAME_TAG,
    SENSOR_NAME_TAG,
)

if TYPE_CHECKING:
    from dagster._core.host_representation.external import ExternalSchedule, ExternalSensor
    from dagster._core.host_representation.origin import ExternalJobOrigin


@whitelist_for_serdes(storage_name="PipelineRunStatus")
class DagsterRunStatus(Enum):
    """The status of run execution."""

    # Runs waiting to be launched by the Dagster Daemon.
    QUEUED = "QUEUED"

    # Runs that have been launched, but execution has not yet started."""
    NOT_STARTED = "NOT_STARTED"

    # Runs that are managed outside of the Dagster control plane.
    MANAGED = "MANAGED"

    # Runs that have been launched, but execution has not yet started.
    STARTING = "STARTING"

    # Runs that have been launched and execution has started.
    STARTED = "STARTED"

    # Runs that have successfully completed.
    SUCCESS = "SUCCESS"

    # Runs that have failed to complete.
    FAILURE = "FAILURE"

    # Runs that are in-progress and pending to be canceled.
    CANCELING = "CANCELING"

    # Runs that have been canceled before completion.
    CANCELED = "CANCELED"


# These statuses that indicate a run may be using compute resources
IN_PROGRESS_RUN_STATUSES = [
    DagsterRunStatus.STARTING,
    DagsterRunStatus.STARTED,
    DagsterRunStatus.CANCELING,
]

# This serves as an explicit list of run statuses that indicate that the run is not using compute
# resources. This and the enum above should cover all run statuses.
NON_IN_PROGRESS_RUN_STATUSES = [
    DagsterRunStatus.QUEUED,
    DagsterRunStatus.NOT_STARTED,
    DagsterRunStatus.SUCCESS,
    DagsterRunStatus.FAILURE,
    DagsterRunStatus.MANAGED,
    DagsterRunStatus.CANCELED,
]

FINISHED_STATUSES = [
    DagsterRunStatus.SUCCESS,
    DagsterRunStatus.FAILURE,
    DagsterRunStatus.CANCELED,
]

# Run statuses for runs that can be safely canceled.
# Does not include the other unfinished statuses for the following reasons:
# STARTING: Control has been ceded to the run worker, which will eventually move the run to a STARTED.
# NOT_STARTED: Mostly replaced with STARTING. Runs are only here in the the brief window between
# creating the run and launching or enqueueing it.
CANCELABLE_RUN_STATUSES = [DagsterRunStatus.STARTED, DagsterRunStatus.QUEUED]


@whitelist_for_serdes(storage_name="PipelineRunStatsSnapshot")
class DagsterRunStatsSnapshot(
    NamedTuple(
        "_DagsterRunStatsSnapshot",
        [
            ("run_id", str),
            ("steps_succeeded", int),
            ("steps_failed", int),
            ("materializations", int),
            ("expectations", int),
            ("enqueued_time", Optional[float]),
            ("launch_time", Optional[float]),
            ("start_time", Optional[float]),
            ("end_time", Optional[float]),
        ],
    )
):
    def __new__(
        cls,
        run_id: str,
        steps_succeeded: int,
        steps_failed: int,
        materializations: int,
        expectations: int,
        enqueued_time: Optional[float],
        launch_time: Optional[float],
        start_time: Optional[float],
        end_time: Optional[float],
    ):
        return super(DagsterRunStatsSnapshot, cls).__new__(
            cls,
            run_id=check.str_param(run_id, "run_id"),
            steps_succeeded=check.int_param(steps_succeeded, "steps_succeeded"),
            steps_failed=check.int_param(steps_failed, "steps_failed"),
            materializations=check.int_param(materializations, "materializations"),
            expectations=check.int_param(expectations, "expectations"),
            enqueued_time=check.opt_float_param(enqueued_time, "enqueued_time"),
            launch_time=check.opt_float_param(launch_time, "launch_time"),
            start_time=check.opt_float_param(start_time, "start_time"),
            end_time=check.opt_float_param(end_time, "end_time"),
        )


class DagsterRunSerializer(NamedTupleSerializer["DagsterRun"]):
    # serdes log
    # * removed reexecution_config - serdes logic expected to strip unknown keys so no need to preserve
    # * added pipeline_snapshot_id
    # * renamed previous_run_id -> parent_run_id, added root_run_id
    # * added execution_plan_snapshot_id
    # * removed selector
    # * added solid_subset
    # * renamed solid_subset -> solid_selection, added solids_to_execute
    # * renamed environment_dict -> run_config
    # * added asset_selection
    # * added has_repository_load_data
    def before_unpack(self, context, unpacked_dict: Dict[str, Any]) -> Dict[str, Any]:
        # back compat for environment dict => run_config
        if "environment_dict" in unpacked_dict:
            check.invariant(
                unpacked_dict.get("run_config") is None,
                "Cannot set both run_config and environment_dict. Use run_config parameter.",
            )
            unpacked_dict["run_config"] = unpacked_dict["environment_dict"]
            del unpacked_dict["environment_dict"]

        # back compat for previous_run_id => parent_run_id, root_run_id
        if "previous_run_id" in unpacked_dict and not (
            "parent_run_id" in unpacked_dict and "root_run_id" in unpacked_dict
        ):
            unpacked_dict["parent_run_id"] = unpacked_dict["previous_run_id"]
            unpacked_dict["root_run_id"] = unpacked_dict["previous_run_id"]
            del unpacked_dict["previous_run_id"]

        # back compat for selector => pipeline_name, solids_to_execute
        if "selector" in unpacked_dict:
            selector = unpacked_dict["selector"]

            if not isinstance(selector, ExecutionSelector):
                check.failed(f"unexpected entry for 'select', {selector}")
            selector_name = selector.name
            selector_subset = selector.solid_subset

            job_name = unpacked_dict.get("pipeline_name")
            check.invariant(
                job_name is None or selector_name == job_name,
                (
                    f"Conflicting pipeline name {job_name} in arguments to PipelineRun: "
                    f"selector was passed with pipeline {selector_name}"
                ),
            )
            if job_name is None:
                unpacked_dict["pipeline_name"] = selector_name

            solids_to_execute = unpacked_dict.get("solids_to_execute")
            check.invariant(
                solids_to_execute is None
                or (selector_subset and set(selector_subset) == solids_to_execute),
                (
                    f"Conflicting solids_to_execute {solids_to_execute} in arguments to"
                    f" PipelineRun: selector was passed with subset {selector_subset}"
                ),
            )
            # for old runs that only have selector but no solids_to_execute
            if solids_to_execute is None:
                solids_to_execute = frozenset(selector_subset) if selector_subset else None

        # back compat for solid_subset => solids_to_execute
        if "solid_subset" in unpacked_dict:
            unpacked_dict["solids_to_execute"] = unpacked_dict["solid_subset"]
            del unpacked_dict["solid_subset"]

        return unpacked_dict


@whitelist_for_serdes(
    serializer=DagsterRunSerializer,
    # DagsterRun is serialized as PipelineRun so that it can be read by older (pre 0.13.x) version
    # of Dagster, but is read back in as a DagsterRun.
    storage_name="PipelineRun",
    old_fields={"mode": None},
    storage_field_names={
        "job_name": "pipeline_name",
        "job_snapshot_id": "pipeline_snapshot_id",
        "external_job_origin": "external_pipeline_origin",
        "job_code_origin": "pipeline_code_origin",
        "op_selection": "solid_selection",
        "resolved_op_selection": "solids_to_execute",
    },
)
class DagsterRun(
    NamedTuple(
        "_DagsterRun",
        [
            ("job_name", PublicAttr[str]),
            ("run_id", str),
            ("run_config", Mapping[str, object]),
            ("asset_selection", Optional[AbstractSet[AssetKey]]),
            ("op_selection", Optional[Sequence[str]]),
            ("resolved_op_selection", Optional[AbstractSet[str]]),
            ("step_keys_to_execute", Optional[Sequence[str]]),
            ("status", DagsterRunStatus),
            ("tags", Mapping[str, str]),
            ("root_run_id", Optional[str]),
            ("parent_run_id", Optional[str]),
            ("job_snapshot_id", Optional[str]),
            ("execution_plan_snapshot_id", Optional[str]),
            ("external_job_origin", Optional["ExternalJobOrigin"]),
            ("job_code_origin", Optional[JobPythonOrigin]),
            ("has_repository_load_data", bool),
        ],
    )
):
    """Serializable internal representation of a dagster run, as stored in a
    :py:class:`~dagster._core.storage.runs.RunStorage`.
    """

    def __new__(
        cls,
        job_name: str,
        run_id: Optional[str] = None,
        run_config: Optional[Mapping[str, object]] = None,
        asset_selection: Optional[AbstractSet[AssetKey]] = None,
        op_selection: Optional[Sequence[str]] = None,
        resolved_op_selection: Optional[AbstractSet[str]] = None,
        step_keys_to_execute: Optional[Sequence[str]] = None,
        status: Optional[DagsterRunStatus] = None,
        tags: Optional[Mapping[str, str]] = None,
        root_run_id: Optional[str] = None,
        parent_run_id: Optional[str] = None,
        job_snapshot_id: Optional[str] = None,
        execution_plan_snapshot_id: Optional[str] = None,
        external_job_origin: Optional["ExternalJobOrigin"] = None,
        job_code_origin: Optional[JobPythonOrigin] = None,
        has_repository_load_data: Optional[bool] = None,
    ):
        check.invariant(
            (root_run_id is not None and parent_run_id is not None)
            or (root_run_id is None and parent_run_id is None),
            (
                "Must set both root_run_id and parent_run_id when creating a PipelineRun that "
                "belongs to a run group"
            ),
        )
        # a set which contains the names of the ops to execute
        resolved_op_selection = check.opt_nullable_set_param(
            resolved_op_selection, "resolved_op_selection", of_type=str
        )
        # a list of op queries provided by the user
        # possible to be None when resolved_op_selection is set by the user directly
        op_selection = check.opt_nullable_sequence_param(op_selection, "op_selection", of_type=str)
        check.opt_nullable_sequence_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)

        asset_selection = check.opt_nullable_set_param(
            asset_selection, "asset_selection", of_type=AssetKey
        )

        # Placing this with the other imports causes a cyclic import
        # https://github.com/dagster-io/dagster/issues/3181
        from dagster._core.host_representation.origin import ExternalJobOrigin

        if status == DagsterRunStatus.QUEUED:
            check.inst_param(
                external_job_origin,
                "external_job_origin",
                ExternalJobOrigin,
                "external_job_origin is required for queued runs",
            )

        if run_id is None:
            run_id = make_new_run_id()

        return super(DagsterRun, cls).__new__(
            cls,
            job_name=check.str_param(job_name, "job_name"),
            run_id=check.str_param(run_id, "run_id"),
            run_config=check.opt_mapping_param(run_config, "run_config", key_type=str),
            op_selection=op_selection,
            asset_selection=asset_selection,
            resolved_op_selection=resolved_op_selection,
            step_keys_to_execute=step_keys_to_execute,
            status=check.opt_inst_param(
                status, "status", DagsterRunStatus, DagsterRunStatus.NOT_STARTED
            ),
            tags=check.opt_mapping_param(tags, "tags", key_type=str, value_type=str),
            root_run_id=check.opt_str_param(root_run_id, "root_run_id"),
            parent_run_id=check.opt_str_param(parent_run_id, "parent_run_id"),
            job_snapshot_id=check.opt_str_param(job_snapshot_id, "job_snapshot_id"),
            execution_plan_snapshot_id=check.opt_str_param(
                execution_plan_snapshot_id, "execution_plan_snapshot_id"
            ),
            external_job_origin=check.opt_inst_param(
                external_job_origin, "external_job_origin", ExternalJobOrigin
            ),
            job_code_origin=check.opt_inst_param(
                job_code_origin, "job_code_origin", JobPythonOrigin
            ),
            has_repository_load_data=check.opt_bool_param(
                has_repository_load_data, "has_repository_load_data", default=False
            ),
        )

    def with_status(self, status: DagsterRunStatus) -> Self:
        if status == DagsterRunStatus.QUEUED:
            # Placing this with the other imports causes a cyclic import
            # https://github.com/dagster-io/dagster/issues/3181
            from dagster._core.host_representation.origin import ExternalJobOrigin

            check.inst(
                self.external_job_origin,
                ExternalJobOrigin,
                "external_pipeline_origin is required for queued runs",
            )

        return self._replace(status=status)

    def with_job_origin(self, origin: "ExternalJobOrigin") -> Self:
        from dagster._core.host_representation.origin import ExternalJobOrigin

        check.inst_param(origin, "origin", ExternalJobOrigin)
        return self._replace(external_job_origin=origin)

    def with_tags(self, tags: Mapping[str, str]) -> Self:
        return self._replace(tags=tags)

    def get_root_run_id(self) -> Optional[str]:
        return self.tags.get(ROOT_RUN_ID_TAG)

    def get_parent_run_id(self) -> Optional[str]:
        return self.tags.get(PARENT_RUN_ID_TAG)

    def tags_for_storage(self) -> Mapping[str, str]:
        repository_tags = {}
        if self.external_job_origin:
            # tag the run with a label containing the repository name / location name, to allow for
            # per-repository filtering of runs from the Dagster UI.
            repository_tags[
                REPOSITORY_LABEL_TAG
            ] = self.external_job_origin.external_repository_origin.get_label()

        if not self.tags:
            return repository_tags

        return {**repository_tags, **self.tags}

    @public
    @property
    def is_finished(self) -> bool:
        """bool: If this run has completely finished execution."""
        return self.status in FINISHED_STATUSES

    @public
    @property
    def is_success(self) -> bool:
        """bool: If this run has successfully finished executing."""
        return self.status == DagsterRunStatus.SUCCESS

    @public
    @property
    def is_failure(self) -> bool:
        """bool: If this run has failed."""
        return self.status == DagsterRunStatus.FAILURE

    @public
    @property
    def is_failure_or_canceled(self) -> bool:
        """bool: If this run has either failed or was canceled."""
        return self.status == DagsterRunStatus.FAILURE or self.status == DagsterRunStatus.CANCELED

    @public
    @property
    def is_resume_retry(self) -> bool:
        """bool: If this run was created from retrying another run from the point of failure."""
        return self.tags.get(RESUME_RETRY_TAG) == "true"

    @property
    def previous_run_id(self) -> Optional[str]:
        # Compat
        return self.parent_run_id

    @staticmethod
    def tags_for_schedule(schedule) -> Mapping[str, str]:
        return {SCHEDULE_NAME_TAG: schedule.name}

    @staticmethod
    def tags_for_sensor(sensor) -> Mapping[str, str]:
        return {SENSOR_NAME_TAG: sensor.name}

    @staticmethod
    def tags_for_backfill_id(backfill_id: str) -> Mapping[str, str]:
        return {BACKFILL_ID_TAG: backfill_id}


class RunsFilterSerializer(NamedTupleSerializer["RunsFilter"]):
    def before_unpack(
        self,
        context,
        unpacked_dict: Dict[str, Any],
    ) -> Dict[str, Any]:
        # We store empty run ids as [] but only accept None
        if "run_ids" in unpacked_dict and unpacked_dict["run_ids"] == []:
            unpacked_dict["run_ids"] = None
        return unpacked_dict


@whitelist_for_serdes(
    serializer=RunsFilterSerializer,
    old_storage_names={"PipelineRunsFilter"},
    storage_field_names={"job_name": "pipeline_name"},
)
class RunsFilter(
    NamedTuple(
        "_RunsFilter",
        [
            ("run_ids", Sequence[str]),
            ("job_name", Optional[str]),
            ("statuses", Sequence[DagsterRunStatus]),
            ("tags", Mapping[str, Union[str, Sequence[str]]]),
            ("snapshot_id", Optional[str]),
            ("updated_after", Optional[datetime]),
            ("updated_before", Optional[datetime]),
            ("created_after", Optional[datetime]),
            ("created_before", Optional[datetime]),
        ],
    )
):
    """Defines a filter across job runs, for use when querying storage directly.

    Each field of the RunsFilter represents a logical AND with each other. For
    example, if you specify job_name and tags, then you will receive only runs
    with the specified job_name AND the specified tags. If left blank, then
    all values will be permitted for that field.

    Args:
        run_ids (Optional[List[str]]): A list of job run_id values.
        job_name (Optional[str]):
            Name of the job to query for. If blank, all job_names will be accepted.
        statuses (Optional[List[DagsterRunStatus]]):
            A list of run statuses to filter by. If blank, all run statuses will be allowed.
        tags (Optional[Dict[str, Union[str, List[str]]]]):
            A dictionary of run tags to query by. All tags specified here must be present for a given run to pass the filter.
        snapshot_id (Optional[str]): The ID of the job snapshot to query for. Intended for internal use.
        updated_after (Optional[DateTime]): Filter by runs that were last updated before this datetime.
        created_before (Optional[DateTime]): Filter by runs that were created before this datetime.

    """

    def __new__(
        cls,
        run_ids: Optional[Sequence[str]] = None,
        job_name: Optional[str] = None,
        statuses: Optional[Sequence[DagsterRunStatus]] = None,
        tags: Optional[Mapping[str, Union[str, Sequence[str]]]] = None,
        snapshot_id: Optional[str] = None,
        updated_after: Optional[datetime] = None,
        updated_before: Optional[datetime] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
    ):
        check.invariant(run_ids != [], "When filtering on run ids, a non-empty list must be used.")

        return super(RunsFilter, cls).__new__(
            cls,
            run_ids=check.opt_sequence_param(run_ids, "run_ids", of_type=str),
            job_name=check.opt_str_param(job_name, "job_name"),
            statuses=check.opt_sequence_param(statuses, "statuses", of_type=DagsterRunStatus),
            tags=check.opt_mapping_param(tags, "tags", key_type=str),
            snapshot_id=check.opt_str_param(snapshot_id, "snapshot_id"),
            updated_after=check.opt_inst_param(updated_after, "updated_after", datetime),
            updated_before=check.opt_inst_param(updated_before, "updated_before", datetime),
            created_after=check.opt_inst_param(created_after, "created_after", datetime),
            created_before=check.opt_inst_param(created_before, "created_before", datetime),
        )

    @staticmethod
    def for_schedule(schedule: "ExternalSchedule") -> "RunsFilter":
        return RunsFilter(tags=DagsterRun.tags_for_schedule(schedule))

    @staticmethod
    def for_sensor(sensor: "ExternalSensor") -> "RunsFilter":
        return RunsFilter(tags=DagsterRun.tags_for_sensor(sensor))

    @staticmethod
    def for_backfill(backfill_id: str) -> "RunsFilter":
        return RunsFilter(tags=DagsterRun.tags_for_backfill_id(backfill_id))


class JobBucket(NamedTuple):
    job_names: List[str]
    bucket_limit: Optional[int]


class TagBucket(NamedTuple):
    tag_key: str
    tag_values: List[str]
    bucket_limit: Optional[int]


class RunRecord(
    NamedTuple(
        "_RunRecord",
        [
            ("storage_id", int),
            ("dagster_run", DagsterRun),
            ("create_timestamp", datetime),
            ("update_timestamp", datetime),
            ("start_time", Optional[float]),
            ("end_time", Optional[float]),
        ],
    )
):
    """Internal representation of a run record, as stored in a
    :py:class:`~dagster._core.storage.runs.RunStorage`.

    Users should not invoke this class directly.
    """

    def __new__(
        cls,
        storage_id: int,
        dagster_run: DagsterRun,
        create_timestamp: datetime,
        update_timestamp: datetime,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ):
        return super(RunRecord, cls).__new__(
            cls,
            storage_id=check.int_param(storage_id, "storage_id"),
            dagster_run=check.inst_param(dagster_run, "dagster_run", DagsterRun),
            create_timestamp=check.inst_param(create_timestamp, "create_timestamp", datetime),
            update_timestamp=check.inst_param(update_timestamp, "update_timestamp", datetime),
            # start_time and end_time fields will be populated once the run has started and ended, respectively, but will be None beforehand.
            start_time=check.opt_float_param(start_time, "start_time"),
            end_time=check.opt_float_param(end_time, "end_time"),
        )


@whitelist_for_serdes
class RunPartitionData(
    NamedTuple(
        "_RunPartitionData",
        [
            ("run_id", str),
            ("partition", str),
            ("status", DagsterRunStatus),
            ("start_time", Optional[float]),
            ("end_time", Optional[float]),
        ],
    )
):
    def __new__(
        cls,
        run_id: str,
        partition: str,
        status: DagsterRunStatus,
        start_time: Optional[float],
        end_time: Optional[float],
    ):
        return super(RunPartitionData, cls).__new__(
            cls,
            run_id=check.str_param(run_id, "run_id"),
            partition=check.str_param(partition, "partition"),
            status=check.inst_param(status, "status", DagsterRunStatus),
            start_time=check.opt_inst(start_time, float),
            end_time=check.opt_inst(end_time, float),
        )


###################################################################################################
# GRAVEYARD
#
#            -|-
#             |
#        _-'~~~~~`-_
#      .'           '.
#      |    R I P    |
#      |             |
#      |  Execution  |
#      |  Selector   |
#      |             |
#      |             |
###################################################################################################


@whitelist_for_serdes
class ExecutionSelector(
    NamedTuple("_ExecutionSelector", [("name", str), ("solid_subset", Optional[Sequence[str]])])
):
    """Kept here to maintain loading of PipelineRuns from when it was still alive."""

    def __new__(cls, name: str, solid_subset: Optional[Sequence[str]] = None):
        return super(ExecutionSelector, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            solid_subset=None
            if solid_subset is None
            else check.sequence_param(solid_subset, "solid_subset", of_type=str),
        )
