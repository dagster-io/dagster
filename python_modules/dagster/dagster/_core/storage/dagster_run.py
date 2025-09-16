import os
from collections.abc import Iterable, Mapping, Sequence, Set
from datetime import datetime
from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, AbstractSet, Any, NamedTuple, Optional, Union  # noqa: UP035

from dagster_shared.record import IHaveNew, LegacyNamedTupleMixin, copy, record, record_custom
from dagster_shared.serdes import NamedTupleSerializer, whitelist_for_serdes
from typing_extensions import Self

import dagster._check as check
from dagster._annotations import PublicAttr, public
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.partitions.subset import (
    KeyRangesPartitionsSubset,
    PartitionsSubset,
    TimeWindowPartitionsSubset,
)
from dagster._core.loader import LoadableBy, LoadingContext
from dagster._core.origin import JobPythonOrigin
from dagster._core.remote_origin import RemoteJobOrigin
from dagster._core.storage.tags import (
    ASSET_EVALUATION_ID_TAG,
    AUTO_RETRY_RUN_ID_TAG,
    AUTOMATION_CONDITION_TAG,
    BACKFILL_ID_TAG,
    PARENT_RUN_ID_TAG,
    POOL_TAG_PREFIX,
    REPOSITORY_LABEL_TAG,
    RESUME_RETRY_TAG,
    ROOT_RUN_ID_TAG,
    SCHEDULE_NAME_TAG,
    SENSOR_NAME_TAG,
    TICK_ID_TAG,
    WILL_RETRY_TAG,
)
from dagster._core.utils import make_new_run_id
from dagster._utils.tags import get_boolean_tag_value

if TYPE_CHECKING:
    from dagster._core.definitions.schedule_definition import ScheduleDefinition
    from dagster._core.definitions.sensor_definition import SensorDefinition
    from dagster._core.remote_representation.external import RemoteSchedule, RemoteSensor
    from dagster._core.scheduler.instigation import InstigatorState


@whitelist_for_serdes(storage_name="PipelineRunStatus")
@public
class DagsterRunStatus(Enum):
    """The status of run execution."""

    # Runs waiting to be launched by the Dagster Daemon.
    QUEUED = "QUEUED"

    # Runs in the brief window between creating the run and launching or enqueueing it.
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

NOT_FINISHED_STATUSES = [
    DagsterRunStatus.STARTING,
    DagsterRunStatus.STARTED,
    DagsterRunStatus.CANCELING,
    DagsterRunStatus.QUEUED,
    DagsterRunStatus.NOT_STARTED,
]

# Run statuses for runs that can be safely canceled.
# Does not include the other unfinished statuses for the following reasons:
# STARTING: Control has been ceded to the run worker, which will eventually move the run to a STARTED.
# NOT_STARTED: Mostly replaced with STARTING. Runs are only here in the brief window between
# creating the run and launching or enqueueing it.
CANCELABLE_RUN_STATUSES = [DagsterRunStatus.STARTED, DagsterRunStatus.QUEUED]


@whitelist_for_serdes(storage_name="PipelineRunStatsSnapshot")
@record
class DagsterRunStatsSnapshot(IHaveNew):
    run_id: str
    steps_succeeded: int
    steps_failed: int
    materializations: int
    expectations: int
    enqueued_time: Optional[float]
    launch_time: Optional[float]
    start_time: Optional[float]
    end_time: Optional[float]


@whitelist_for_serdes
@record
class RunOpConcurrency(IHaveNew):
    """Utility class to help calculate the immediate impact of launching a run on the op concurrency
    slots that will be available for other runs.
    """

    root_key_counts: Mapping[str, int]
    has_unconstrained_root_nodes: bool
    all_pools: Optional[Set[str]] = None


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
    def before_unpack(self, context, unpacked_dict: dict[str, Any]) -> dict[str, Any]:
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
                f"Conflicting pipeline name {job_name} in arguments to PipelineRun: "
                f"selector was passed with pipeline {selector_name}",
            )
            if job_name is None:
                unpacked_dict["pipeline_name"] = selector_name

            solids_to_execute = unpacked_dict.get("solids_to_execute")
            check.invariant(
                solids_to_execute is None
                or (selector_subset and set(selector_subset) == solids_to_execute),
                f"Conflicting solids_to_execute {solids_to_execute} in arguments to"
                f" PipelineRun: selector was passed with subset {selector_subset}",
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
        "remote_job_origin": "external_pipeline_origin",
        "job_code_origin": "pipeline_code_origin",
        "op_selection": "solid_selection",
        "resolved_op_selection": "solids_to_execute",
    },
)
@public
@record_custom
class DagsterRun(
    IHaveNew,
    LegacyNamedTupleMixin,
):
    """Serializable internal representation of a dagster run, as stored in a
    :py:class:`~dagster._core.storage.runs.RunStorage`.

    Args:
        job_name (str): The name of the job executed in this run.
        run_id (str): The ID of the run.
        run_config (Mapping[str, object]): The config for the run.
        asset_selection (Optional[AbstractSet[AssetKey]]): The assets selected for this run.
        asset_check_selection (Optional[AbstractSet[AssetCheckKey]]): The asset checks selected for this run.
        op_selection (Optional[Sequence[str]]): The op queries provided by the user.
        resolved_op_selection (Optional[AbstractSet[str]]): The resolved set of op names to execute.
        step_keys_to_execute (Optional[Sequence[str]]): The step keys to execute.
        status (DagsterRunStatus): The status of the run.
        tags (Mapping[str, str]): The tags applied to the run.
        root_run_id (Optional[str]): The ID of the root run in the run's group.
        parent_run_id (Optional[str]): The ID of the parent run in the run's group.
        job_snapshot_id (Optional[str]): The ID of the job snapshot.
        execution_plan_snapshot_id (Optional[str]): The ID of the execution plan snapshot.
        remote_job_origin (Optional[RemoteJobOrigin]): The origin of the executed job.
        job_code_origin (Optional[JobPythonOrigin]): The origin of the job code.
        has_repository_load_data (bool): Whether the run has repository load data.
        run_op_concurrency (Optional[RunOpConcurrency]): The op concurrency information for the run.
        partitions_subset (Optional[PartitionsSubset]): The subset of partitions to execute.
    """

    job_name: PublicAttr[str]
    run_id: PublicAttr[str]
    run_config: PublicAttr[Mapping[str, object]]
    asset_selection: Optional[AbstractSet[AssetKey]]
    asset_check_selection: Optional[AbstractSet[AssetCheckKey]]
    op_selection: Optional[Sequence[str]]
    resolved_op_selection: Optional[AbstractSet[str]]
    step_keys_to_execute: Optional[Sequence[str]]
    status: PublicAttr[DagsterRunStatus]
    tags: PublicAttr[Mapping[str, str]]
    root_run_id: Optional[str]
    parent_run_id: Optional[str]
    job_snapshot_id: Optional[str]
    execution_plan_snapshot_id: Optional[str]
    remote_job_origin: Optional[RemoteJobOrigin]
    job_code_origin: Optional[JobPythonOrigin]
    has_repository_load_data: bool
    run_op_concurrency: Optional[RunOpConcurrency]

    # Only support storing certain partitions subsets on the run for now, other
    # partitions subsets are too big.
    # NOTE: if you are expanding the valid set, be mindful of older versions not handling it.
    partitions_subset: Optional[Union[TimeWindowPartitionsSubset, KeyRangesPartitionsSubset]]

    def __new__(
        cls,
        job_name: str,
        run_id: Optional[str] = None,
        run_config: Optional[Mapping[str, object]] = None,
        asset_selection: Optional[AbstractSet[AssetKey]] = None,
        asset_check_selection: Optional[AbstractSet[AssetCheckKey]] = None,
        op_selection: Optional[Sequence[str]] = None,
        resolved_op_selection: Optional[AbstractSet[str]] = None,
        step_keys_to_execute: Optional[Sequence[str]] = None,
        status: Optional[DagsterRunStatus] = None,
        tags: Optional[Mapping[str, str]] = None,
        root_run_id: Optional[str] = None,
        parent_run_id: Optional[str] = None,
        job_snapshot_id: Optional[str] = None,
        execution_plan_snapshot_id: Optional[str] = None,
        remote_job_origin: Optional[RemoteJobOrigin] = None,
        job_code_origin: Optional[JobPythonOrigin] = None,
        has_repository_load_data: Optional[bool] = None,
        run_op_concurrency: Optional[RunOpConcurrency] = None,
        partitions_subset: Optional[PartitionsSubset] = None,
    ):
        check.invariant(
            (root_run_id is not None and parent_run_id is not None)
            or (root_run_id is None and parent_run_id is None),
            "Must set both root_run_id and parent_run_id when creating a PipelineRun that "
            "belongs to a run group",
        )

        if status == DagsterRunStatus.QUEUED:
            check.inst_param(
                remote_job_origin,
                "remote_job_origin",
                RemoteJobOrigin,
                "remote_job_origin is required for queued runs",
            )

        if run_id is None:
            run_id = make_new_run_id()

        return super().__new__(
            cls,
            job_name=job_name,
            run_id=run_id,
            run_config={} if run_config is None else run_config,
            op_selection=op_selection,
            asset_selection=asset_selection,
            asset_check_selection=asset_check_selection,
            resolved_op_selection=resolved_op_selection,
            step_keys_to_execute=step_keys_to_execute,
            status=DagsterRunStatus.NOT_STARTED if status is None else status,
            tags={} if tags is None else tags,
            root_run_id=root_run_id,
            parent_run_id=parent_run_id,
            job_snapshot_id=job_snapshot_id,
            execution_plan_snapshot_id=execution_plan_snapshot_id,
            remote_job_origin=remote_job_origin,
            job_code_origin=job_code_origin,
            has_repository_load_data=False
            if has_repository_load_data is None
            else has_repository_load_data,
            run_op_concurrency=run_op_concurrency,
            partitions_subset=partitions_subset,
        )

    def with_status(self, status: DagsterRunStatus) -> Self:
        if status == DagsterRunStatus.QUEUED:
            # Placing this with the other imports causes a cyclic import
            # https://github.com/dagster-io/dagster/issues/3181

            check.not_none(
                self.remote_job_origin,
                "external_pipeline_origin is required for queued runs",
            )

        return copy(self, status=status)

    def with_job_origin(self, origin: "RemoteJobOrigin") -> Self:
        return copy(self, remote_job_origin=origin)

    def with_tags(self, tags: Mapping[str, str]) -> Self:
        return copy(self, tags=tags)

    def get_root_run_id(self) -> Optional[str]:
        return self.tags.get(ROOT_RUN_ID_TAG)

    def get_parent_run_id(self) -> Optional[str]:
        return self.tags.get(PARENT_RUN_ID_TAG)

    @cached_property
    def dagster_execution_info(self) -> Mapping[str, str]:
        """Key-value pairs encoding metadata about the current Dagster run, typically attached to external execution resources.

        Remote execution environments commonly have their own concepts of tags or labels. It's useful to include
        Dagster-specific metadata in these environments to help with debugging, monitoring, and linking remote
        resources back to Dagster. For example, the Kubernetes Executor and Pipes client are using these tags as Kubernetes labels.

        By default the tags include:
        * dagster/run-id
        * dagster/job

        And, if available:
        * dagster/partition
        * dagster/code-location
        * dagster/user

        And, for Dagster+ deployments:
        * dagster/deployment-name
        * dagster/git-repo
        * dagster/git-branch
        * dagster/git-sha
        """
        tags = {
            "dagster/run-id": self.run_id,
            "dagster/job": self.job_name,
        }

        if self.remote_job_origin:
            tags["dagster/code-location"] = (
                self.remote_job_origin.repository_origin.code_location_origin.location_name
            )

        if user := self.tags.get("dagster/user"):
            tags["dagster/user"] = user

        if partition := self.tags.get("dagster/partition"):
            tags["dagster/partition"] = partition

        for env_var, tag in {
            "DAGSTER_CLOUD_DEPLOYMENT_NAME": "deployment-name",
            "DAGSTER_CLOUD_GIT_REPO": "git-repo",
            "DAGSTER_CLOUD_GIT_BRANCH": "git-branch",
            "DAGSTER_CLOUD_GIT_SHA": "git-sha",
        }.items():
            if value := os.getenv(env_var):
                tags[f"dagster/{tag}"] = value

        return tags

    def tags_for_storage(self) -> Mapping[str, str]:
        repository_tags = {}
        if self.remote_job_origin:
            # tag the run with a label containing the repository name / location name, to allow for
            # per-repository filtering of runs from the Dagster UI.
            repository_tags[REPOSITORY_LABEL_TAG] = (
                self.remote_job_origin.repository_origin.get_label()
            )

        pool_tags = {}
        if self.run_op_concurrency and self.run_op_concurrency.all_pools:
            pool_tags = {
                f"{POOL_TAG_PREFIX}{pool}": "true" for pool in self.run_op_concurrency.all_pools
            }

        return {**repository_tags, **pool_tags, **(self.tags or {})}

    @public
    @property
    def is_finished(self) -> bool:
        """bool: If this run has completely finished execution."""
        return self.status in FINISHED_STATUSES

    @public
    @property
    def is_cancelable(self) -> bool:
        """bool: If this run an be canceled."""
        return self.status in CANCELABLE_RUN_STATUSES

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
    def is_complete_and_waiting_to_retry(self):
        """Indicates if a run is waiting to be retried by the auto-reexecution system.
        Returns True if 1) the run is complete, 2) the run is in a failed state (therefore eligible for retry),
        3) the run is marked as needing to be retried, and 4) the retried run has not been launched yet.
        Otherwise returns False.
        """
        if self.status in NOT_FINISHED_STATUSES:
            return False
        if self.status != DagsterRunStatus.FAILURE:
            return False
        will_retry = get_boolean_tag_value(self.tags.get(WILL_RETRY_TAG), default_value=False)
        retry_not_launched = self.tags.get(AUTO_RETRY_RUN_ID_TAG) is None
        if will_retry:
            return retry_not_launched

        return False

    @property
    def previous_run_id(self) -> Optional[str]:
        # Compat
        return self.parent_run_id

    @staticmethod
    def tags_for_schedule(
        schedule: Union["InstigatorState", "RemoteSchedule", "ScheduleDefinition"],
    ) -> Mapping[str, str]:
        return {SCHEDULE_NAME_TAG: schedule.name}

    @staticmethod
    def tags_for_sensor(
        sensor: Union["InstigatorState", "RemoteSensor", "SensorDefinition"],
    ) -> Mapping[str, str]:
        return {SENSOR_NAME_TAG: sensor.name}

    @staticmethod
    def tags_for_backfill_id(backfill_id: str) -> Mapping[str, str]:
        return {BACKFILL_ID_TAG: backfill_id}

    @staticmethod
    def tags_for_tick_id(tick_id: str, has_evaluations: bool = False) -> Mapping[str, str]:
        if has_evaluations:
            automation_tags = {AUTOMATION_CONDITION_TAG: "true", ASSET_EVALUATION_ID_TAG: tick_id}
        else:
            automation_tags = {}
        return {TICK_ID_TAG: tick_id, **automation_tags}


@public
@record_custom
class RunsFilter(IHaveNew):
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
        exclude_subruns (Optional[bool]): If true, runs that were launched to backfill historical data will be excluded from results.
    """

    run_ids: Optional[Sequence[str]]
    job_name: Optional[str]
    statuses: Sequence[DagsterRunStatus]
    tags: Mapping[str, Union[str, Sequence[str]]]
    snapshot_id: Optional[str]
    updated_after: Optional[datetime]
    updated_before: Optional[datetime]
    created_after: Optional[datetime]
    created_before: Optional[datetime]
    exclude_subruns: Optional[bool]

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
        exclude_subruns: Optional[bool] = None,
    ):
        check.invariant(run_ids != [], "When filtering on run ids, a non-empty list must be used.")

        return super().__new__(
            cls,
            run_ids=run_ids,
            job_name=job_name,
            statuses=statuses or [],
            tags=tags or {},
            snapshot_id=snapshot_id,
            updated_after=updated_after,
            updated_before=updated_before,
            created_after=created_after,
            created_before=created_before,
            exclude_subruns=exclude_subruns,
        )

    @staticmethod
    def for_schedule(
        schedule: Union["RemoteSchedule", "InstigatorState", "ScheduleDefinition"],
    ) -> "RunsFilter":
        return RunsFilter(tags=DagsterRun.tags_for_schedule(schedule))

    @staticmethod
    def for_sensor(
        sensor: Union["RemoteSensor", "InstigatorState", "SensorDefinition"],
    ) -> "RunsFilter":
        return RunsFilter(tags=DagsterRun.tags_for_sensor(sensor))

    @staticmethod
    def for_backfill(backfill_id: str) -> "RunsFilter":
        return RunsFilter(tags=DagsterRun.tags_for_backfill_id(backfill_id))


class JobBucket(NamedTuple):
    job_names: list[str]
    bucket_limit: Optional[int]


class TagBucket(NamedTuple):
    tag_key: str
    tag_values: list[str]
    bucket_limit: Optional[int]


@public
@record(kw_only=False)
class RunRecord(
    IHaveNew,
    LegacyNamedTupleMixin,
    LoadableBy[str],
):
    """Internal representation of a run record, as stored in a
    :py:class:`~dagster._core.storage.runs.RunStorage`.

    Users should not invoke this class directly.
    """

    storage_id: int
    dagster_run: DagsterRun
    create_timestamp: datetime
    update_timestamp: datetime
    # start_time and end_time fields will be populated once the run has started and ended, respectively, but will be None beforehand.
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    @classmethod
    def _blocking_batch_load(
        cls, keys: Iterable[str], context: LoadingContext
    ) -> Iterable[Optional["RunRecord"]]:
        result_map: dict[str, Optional[RunRecord]] = {run_id: None for run_id in keys}

        run_ids = list(result_map.keys())

        records = []
        batch_size = int(os.getenv("DAGSTER_RUN_RECORD_LOADER_BATCH_SIZE", "100"))
        for i in range(0, len(run_ids), batch_size):
            chunk = run_ids[i : i + batch_size]
            chunk_records = context.instance.get_run_records(RunsFilter(run_ids=chunk))
            records.extend([record for record in chunk_records if record])

        for r in records:
            result_map[r.dagster_run.run_id] = r

        return [result_map[k] for k in keys]


@whitelist_for_serdes
@record
class RunPartitionData:
    run_id: str
    partition: str
    status: DagsterRunStatus
    start_time: Optional[float]
    end_time: Optional[float]


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
@record
class ExecutionSelector:
    """Kept here to maintain loading of PipelineRuns from when it was still alive."""

    name: str
    solid_subset: Optional[Sequence[str]] = None


def assets_are_externally_managed(run: DagsterRun) -> bool:
    from dagster._core.storage.tags import EXTERNALLY_MANAGED_ASSETS_TAG

    return get_boolean_tag_value(run.tags.get(EXTERNALLY_MANAGED_ASSETS_TAG), default_value=False)
