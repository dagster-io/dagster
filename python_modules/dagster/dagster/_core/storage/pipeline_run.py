import warnings
from datetime import datetime
from enum import Enum
from inspect import Parameter
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    FrozenSet,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Type,
    Union,
)

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions.events import AssetKey
from dagster._core.origin import PipelinePythonOrigin
from dagster._core.storage.tags import PARENT_RUN_ID_TAG, ROOT_RUN_ID_TAG
from dagster._core.utils import make_new_run_id
from dagster._serdes.serdes import (
    DefaultNamedTupleSerializer,
    EnumSerializer,
    WhitelistMap,
    register_serdes_enum_fallbacks,
    register_serdes_tuple_fallbacks,
    replace_storage_keys,
    unpack_inner_value,
    whitelist_for_serdes,
)

from .tags import (
    BACKFILL_ID_TAG,
    PARTITION_NAME_TAG,
    PARTITION_SET_TAG,
    REPOSITORY_LABEL_TAG,
    RESUME_RETRY_TAG,
    SCHEDULE_NAME_TAG,
    SENSOR_NAME_TAG,
)

if TYPE_CHECKING:
    from dagster._core.definitions.repository_definition import RepositoryLoadData
    from dagster._core.host_representation.origin import ExternalPipelineOrigin


class DagsterRunStatusSerializer(EnumSerializer):
    @classmethod
    def value_from_storage_str(cls, storage_str: str, klass: Type) -> Enum:
        return getattr(klass, storage_str)

    @classmethod
    def value_to_storage_str(
        cls, value: Enum, whitelist_map: WhitelistMap, descent_path: str
    ) -> str:
        enum_value = value.value
        # Store DagsterRunStatus with backcompat name PipelineRunStatus
        backcompat_name = "PipelineRunStatus"
        return ".".join([backcompat_name, enum_value])


@whitelist_for_serdes(serializer=DagsterRunStatusSerializer)
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


PipelineRunStatus = DagsterRunStatus
register_serdes_enum_fallbacks({"PipelineRunStatus": DagsterRunStatus})

# These statuses that indicate a run may be using compute resources
IN_PROGRESS_RUN_STATUSES = [
    PipelineRunStatus.STARTING,
    PipelineRunStatus.STARTED,
    PipelineRunStatus.CANCELING,
]

# This serves as an explicit list of run statuses that indicate that the run is not using compute
# resources. This and the enum above should cover all run statuses.
NON_IN_PROGRESS_RUN_STATUSES = [
    PipelineRunStatus.QUEUED,
    PipelineRunStatus.NOT_STARTED,
    PipelineRunStatus.SUCCESS,
    PipelineRunStatus.FAILURE,
    PipelineRunStatus.MANAGED,
    PipelineRunStatus.CANCELED,
]

FINISHED_STATUSES = [
    PipelineRunStatus.SUCCESS,
    PipelineRunStatus.FAILURE,
    PipelineRunStatus.CANCELED,
]


@whitelist_for_serdes
class PipelineRunStatsSnapshot(
    NamedTuple(
        "_PipelineRunStatsSnapshot",
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
        return super(PipelineRunStatsSnapshot, cls).__new__(
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


class DagsterRunSerializer(DefaultNamedTupleSerializer):
    @classmethod
    def value_from_storage_dict(
        cls,
        storage_dict,
        klass,
        args_for_class,
        whitelist_map,
        descent_path,
    ):
        # unpack all stored fields
        unpacked_dict = {
            key: unpack_inner_value(value, whitelist_map, f"{descent_path}.{key}")
            for key, value in storage_dict.items()
        }
        # called by the serdes layer, delegates to helper method with expanded kwargs
        return pipeline_run_from_storage(**unpacked_dict)

    @classmethod
    def value_to_storage_dict(
        cls,
        value: NamedTuple,
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> Dict[str, Any]:
        storage = super().value_to_storage_dict(
            value,
            whitelist_map,
            descent_path,
        )
        # persist using legacy name PipelineRun
        storage["__class__"] = "PipelineRun"
        return storage


def pipeline_run_from_storage(
    pipeline_name=None,
    run_id=None,
    run_config=None,
    mode=None,
    asset_selection=None,
    solid_selection=None,
    solids_to_execute=None,
    step_keys_to_execute=None,
    status=None,
    tags=None,
    root_run_id=None,
    parent_run_id=None,
    pipeline_snapshot_id=None,
    execution_plan_snapshot_id=None,
    # backcompat
    environment_dict=None,
    previous_run_id=None,
    selector=None,
    solid_subset=None,
    reexecution_config=None,  # pylint: disable=unused-argument
    external_pipeline_origin=None,
    pipeline_code_origin=None,
    has_repository_load_data=None,
    **kwargs,
):

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

    # back compat for environment dict => run_config
    if environment_dict:
        check.invariant(
            not run_config,
            "Cannot set both run_config and environment_dict. Use run_config parameter.",
        )
        run_config = environment_dict

    # back compat for previous_run_id => parent_run_id, root_run_id
    if previous_run_id and not (parent_run_id and root_run_id):
        parent_run_id = previous_run_id
        root_run_id = previous_run_id

    # back compat for selector => pipeline_name, solids_to_execute
    selector = check.opt_inst_param(selector, "selector", ExecutionSelector)
    if selector:
        check.invariant(
            pipeline_name is None or selector.name == pipeline_name,
            (
                "Conflicting pipeline name {pipeline_name} in arguments to PipelineRun: "
                "selector was passed with pipeline {selector_pipeline}".format(
                    pipeline_name=pipeline_name, selector_pipeline=selector.name
                )
            ),
        )
        if pipeline_name is None:
            pipeline_name = selector.name

        check.invariant(
            solids_to_execute is None or set(selector.solid_subset) == solids_to_execute,
            (
                "Conflicting solids_to_execute {solids_to_execute} in arguments to PipelineRun: "
                "selector was passed with subset {selector_subset}".format(
                    solids_to_execute=solids_to_execute, selector_subset=selector.solid_subset
                )
            ),
        )
        # for old runs that only have selector but no solids_to_execute
        if solids_to_execute is None:
            solids_to_execute = frozenset(selector.solid_subset) if selector.solid_subset else None

    # back compat for solid_subset => solids_to_execute
    check.opt_list_param(solid_subset, "solid_subset", of_type=str)
    if solid_subset:
        solids_to_execute = frozenset(solid_subset)

    # warn about unused arguments
    if len(kwargs):
        warnings.warn(
            "Found unhandled arguments from stored PipelineRun: {args}".format(args=kwargs.keys())
        )

    return DagsterRun(  # pylint: disable=redundant-keyword-arg
        pipeline_name=pipeline_name,
        run_id=run_id,
        run_config=run_config,
        mode=mode,
        asset_selection=asset_selection,
        solid_selection=solid_selection,
        solids_to_execute=solids_to_execute,
        step_keys_to_execute=step_keys_to_execute,
        status=status,
        tags=tags,
        root_run_id=root_run_id,
        parent_run_id=parent_run_id,
        pipeline_snapshot_id=pipeline_snapshot_id,
        execution_plan_snapshot_id=execution_plan_snapshot_id,
        external_pipeline_origin=external_pipeline_origin,
        pipeline_code_origin=pipeline_code_origin,
        has_repository_load_data=has_repository_load_data,
    )


class PipelineRun(
    NamedTuple(
        "_PipelineRun",
        [
            ("pipeline_name", str),
            ("run_id", str),
            ("run_config", Mapping[str, object]),
            ("mode", Optional[str]),
            ("asset_selection", Optional[FrozenSet[AssetKey]]),
            ("solid_selection", Optional[List[str]]),
            ("solids_to_execute", Optional[FrozenSet[str]]),
            ("step_keys_to_execute", Optional[List[str]]),
            ("status", PipelineRunStatus),
            ("tags", Dict[str, str]),
            ("root_run_id", Optional[str]),
            ("parent_run_id", Optional[str]),
            ("pipeline_snapshot_id", Optional[str]),
            ("execution_plan_snapshot_id", Optional[str]),
            ("external_pipeline_origin", Optional["ExternalPipelineOrigin"]),
            ("pipeline_code_origin", Optional[PipelinePythonOrigin]),
            ("has_repository_load_data", bool),
        ],
    )
):
    """Serializable internal representation of a pipeline run, as stored in a
    :py:class:`~dagster._core.storage.runs.RunStorage`.
    """

    def __new__(
        cls,
        pipeline_name: str,
        run_id: Optional[str] = None,
        run_config: Optional[Mapping[str, object]] = None,
        mode: Optional[str] = None,
        asset_selection: Optional[FrozenSet[AssetKey]] = None,
        solid_selection: Optional[List[str]] = None,
        solids_to_execute: Optional[FrozenSet[str]] = None,
        step_keys_to_execute: Optional[List[str]] = None,
        status: Optional[PipelineRunStatus] = None,
        tags: Optional[Dict[str, str]] = None,
        root_run_id: Optional[str] = None,
        parent_run_id: Optional[str] = None,
        pipeline_snapshot_id: Optional[str] = None,
        execution_plan_snapshot_id: Optional[str] = None,
        external_pipeline_origin: Optional["ExternalPipelineOrigin"] = None,
        pipeline_code_origin: Optional[PipelinePythonOrigin] = None,
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
        # a frozenset which contains the names of the solids to execute
        solids_to_execute = check.opt_nullable_set_param(
            solids_to_execute, "solids_to_execute", of_type=str
        )
        # a list of solid queries provided by the user
        # possible to be None when only solids_to_execute is set by the user directly
        solid_selection = check.opt_nullable_list_param(
            solid_selection, "solid_selection", of_type=str
        )
        check.opt_nullable_list_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)

        asset_selection = check.opt_nullable_set_param(
            asset_selection, "asset_selection", of_type=AssetKey
        )

        # Placing this with the other imports causes a cyclic import
        # https://github.com/dagster-io/dagster/issues/3181
        from dagster._core.host_representation.origin import ExternalPipelineOrigin

        if status == PipelineRunStatus.QUEUED:
            check.inst_param(
                external_pipeline_origin,
                "external_pipeline_origin",
                ExternalPipelineOrigin,
                "external_pipeline_origin is required for queued runs",
            )

        if run_id is None:
            run_id = make_new_run_id()

        return super(PipelineRun, cls).__new__(
            cls,
            pipeline_name=check.str_param(pipeline_name, "pipeline_name"),
            run_id=check.str_param(run_id, "run_id"),
            run_config=check.opt_mapping_param(run_config, "run_config", key_type=str),
            mode=check.opt_str_param(mode, "mode"),
            solid_selection=solid_selection,
            asset_selection=asset_selection,
            solids_to_execute=solids_to_execute,
            step_keys_to_execute=step_keys_to_execute,
            status=check.opt_inst_param(
                status, "status", PipelineRunStatus, PipelineRunStatus.NOT_STARTED
            ),
            tags=check.opt_dict_param(tags, "tags", key_type=str, value_type=str),
            root_run_id=check.opt_str_param(root_run_id, "root_run_id"),
            parent_run_id=check.opt_str_param(parent_run_id, "parent_run_id"),
            pipeline_snapshot_id=check.opt_str_param(pipeline_snapshot_id, "pipeline_snapshot_id"),
            execution_plan_snapshot_id=check.opt_str_param(
                execution_plan_snapshot_id, "execution_plan_snapshot_id"
            ),
            external_pipeline_origin=check.opt_inst_param(
                external_pipeline_origin, "external_pipeline_origin", ExternalPipelineOrigin
            ),
            pipeline_code_origin=check.opt_inst_param(
                pipeline_code_origin, "pipeline_code_origin", PipelinePythonOrigin
            ),
            has_repository_load_data=check.opt_bool_param(
                has_repository_load_data, "has_repository_load_data", default=False
            ),
        )

    def with_status(self, status):
        if status == PipelineRunStatus.QUEUED:
            # Placing this with the other imports causes a cyclic import
            # https://github.com/dagster-io/dagster/issues/3181
            from dagster._core.host_representation.origin import ExternalPipelineOrigin

            check.inst(
                self.external_pipeline_origin,
                ExternalPipelineOrigin,
                "external_pipeline_origin is required for queued runs",
            )

        return self._replace(status=status)

    def with_job_origin(self, origin):
        from dagster._core.host_representation.origin import ExternalPipelineOrigin

        check.inst_param(origin, "origin", ExternalPipelineOrigin)
        return self._replace(external_pipeline_origin=origin)

    def with_mode(self, mode):
        return self._replace(mode=mode)

    def with_tags(self, tags):
        return self._replace(tags=tags)

    def get_root_run_id(self):
        return self.tags.get(ROOT_RUN_ID_TAG)

    def get_parent_run_id(self):
        return self.tags.get(PARENT_RUN_ID_TAG)

    def tags_for_storage(self):
        repository_tags = {}
        if self.external_pipeline_origin:
            # tag the run with a label containing the repository name / location name, to allow for
            # per-repository filtering of runs from dagit.
            repository_tags[
                REPOSITORY_LABEL_TAG
            ] = self.external_pipeline_origin.external_repository_origin.get_label()

        if not self.tags:
            return repository_tags

        return {**repository_tags, **self.tags}

    @public  # type: ignore
    @property
    def is_finished(self):
        return self.status in FINISHED_STATUSES

    @public  # type: ignore
    @property
    def is_success(self):
        return self.status == PipelineRunStatus.SUCCESS

    @public  # type: ignore
    @property
    def is_failure(self):
        return self.status == PipelineRunStatus.FAILURE

    @public  # type: ignore
    @property
    def is_failure_or_canceled(self):
        return self.status == PipelineRunStatus.FAILURE or self.status == PipelineRunStatus.CANCELED

    @public  # type: ignore
    @property
    def is_resume_retry(self):
        return self.tags.get(RESUME_RETRY_TAG) == "true"

    @property
    def previous_run_id(self):
        # Compat
        return self.parent_run_id

    @public  # type: ignore
    @property
    def job_name(self) -> str:
        return self.pipeline_name

    @staticmethod
    def tags_for_schedule(schedule):
        return {SCHEDULE_NAME_TAG: schedule.name}

    @staticmethod
    def tags_for_sensor(sensor):
        return {SENSOR_NAME_TAG: sensor.name}

    @staticmethod
    def tags_for_backfill_id(backfill_id):
        return {BACKFILL_ID_TAG: backfill_id}

    @staticmethod
    def tags_for_partition_set(partition_set, partition):
        return {PARTITION_NAME_TAG: partition.name, PARTITION_SET_TAG: partition_set.name}


@whitelist_for_serdes(serializer=DagsterRunSerializer)
class DagsterRun(PipelineRun):
    """Serializable internal representation of a dagster run, as stored in a
    :py:class:`~dagster._core.storage.runs.RunStorage`.

    Subclasses PipelineRun for backcompat purposes. DagsterRun is the actual initialized class used throughout the system.
    """


# DagsterRun is serialized as PipelineRun so that it can be read by older (pre 0.13.x) version of
# Dagster, but is read back in as a DagsterRun.
register_serdes_tuple_fallbacks({"PipelineRun": DagsterRun})


class RunsFilterSerializer(DefaultNamedTupleSerializer):
    @classmethod
    def value_to_storage_dict(
        cls,
        value: NamedTuple,
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> Dict[str, Any]:
        storage = super().value_to_storage_dict(
            value,
            whitelist_map,
            descent_path,
        )
        # For backcompat, we store:
        # job_name as pipeline_name
        return replace_storage_keys(storage, {"job_name": "pipeline_name"})

    @classmethod
    def value_from_storage_dict(
        cls,
        storage_dict: Dict[str, Any],
        klass: Type,
        args_for_class: Mapping[str, Parameter],
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> NamedTuple:
        # We store empty run ids as [] but only accept None
        if "run_ids" in storage_dict and storage_dict["run_ids"] == []:
            storage_dict["run_ids"] = None

        return super().value_from_storage_dict(
            storage_dict, klass, args_for_class, whitelist_map, descent_path
        )


@whitelist_for_serdes(serializer=RunsFilterSerializer)
class RunsFilter(
    NamedTuple(
        "_RunsFilter",
        [
            ("run_ids", List[str]),
            ("job_name", Optional[str]),
            ("statuses", List[DagsterRunStatus]),
            ("tags", Dict[str, Union[str, List[str]]]),
            ("snapshot_id", Optional[str]),
            ("updated_after", Optional[datetime]),
            ("mode", Optional[str]),
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
        mode (Optional[str]): (deprecated)
        pipeline_name (Optional[str]): (deprecated)

    """

    def __new__(
        cls,
        run_ids: Optional[List[str]] = None,
        job_name: Optional[str] = None,
        statuses: Optional[List[DagsterRunStatus]] = None,
        tags: Optional[Dict[str, Union[str, List[str]]]] = None,
        snapshot_id: Optional[str] = None,
        updated_after: Optional[datetime] = None,
        mode: Optional[str] = None,
        created_before: Optional[datetime] = None,
        pipeline_name: Optional[str] = None,  # for backcompat purposes
    ):
        job_name = job_name or pipeline_name

        check.invariant(run_ids != [], "When filtering on run ids, a non-empty list must be used.")

        return super(RunsFilter, cls).__new__(
            cls,
            run_ids=check.opt_list_param(run_ids, "run_ids", of_type=str),
            job_name=check.opt_str_param(job_name, "job_name"),
            statuses=check.opt_list_param(statuses, "statuses", of_type=PipelineRunStatus),
            tags=check.opt_dict_param(tags, "tags", key_type=str),
            snapshot_id=check.opt_str_param(snapshot_id, "snapshot_id"),
            updated_after=check.opt_inst_param(updated_after, "updated_after", datetime),
            mode=check.opt_str_param(mode, "mode"),
            created_before=check.opt_inst_param(created_before, "created_before", datetime),
        )

    @property
    def pipeline_name(self):
        return self.job_name

    @staticmethod
    def for_schedule(schedule):
        return RunsFilter(tags=PipelineRun.tags_for_schedule(schedule))

    @staticmethod
    def for_partition(partition_set, partition):
        return RunsFilter(tags=PipelineRun.tags_for_partition_set(partition_set, partition))

    @staticmethod
    def for_sensor(sensor):
        return RunsFilter(tags=PipelineRun.tags_for_sensor(sensor))

    @staticmethod
    def for_backfill(backfill_id):
        return RunsFilter(tags=PipelineRun.tags_for_backfill_id(backfill_id))


register_serdes_tuple_fallbacks({"PipelineRunsFilter": RunsFilter})
# DEPRECATED - keeping around for backcompat reasons (some folks might have imported directly)
PipelineRunsFilter = RunsFilter


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
            ("pipeline_run", PipelineRun),
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
        storage_id,
        pipeline_run,
        create_timestamp,
        update_timestamp,
        start_time=None,
        end_time=None,
    ):
        return super(RunRecord, cls).__new__(
            cls,
            storage_id=check.int_param(storage_id, "storage_id"),
            pipeline_run=check.inst_param(pipeline_run, "pipeline_run", PipelineRun),
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
    NamedTuple("_ExecutionSelector", [("name", str), ("solid_subset", Optional[List[str]])])
):
    """
    Kept here to maintain loading of PipelineRuns from when it was still alive.
    """

    def __new__(cls, name: str, solid_subset: Optional[List[str]] = None):
        return super(ExecutionSelector, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            solid_subset=None
            if solid_subset is None
            else check.list_param(solid_subset, "solid_subset", of_type=str),
        )
