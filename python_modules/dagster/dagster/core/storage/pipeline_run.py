import warnings
from collections import namedtuple
from enum import Enum

from dagster import check
from dagster.core.storage.tags import PARENT_RUN_ID_TAG, ROOT_RUN_ID_TAG
from dagster.core.utils import make_new_run_id
from dagster.serdes import DefaultNamedTupleSerializer, whitelist_for_serdes

from .tags import (
    BACKFILL_ID_TAG,
    PARTITION_NAME_TAG,
    PARTITION_SET_TAG,
    RESUME_RETRY_TAG,
    SCHEDULE_NAME_TAG,
    SENSOR_NAME_TAG,
)


@whitelist_for_serdes
class PipelineRunStatus(Enum):
    QUEUED = "QUEUED"
    NOT_STARTED = "NOT_STARTED"
    MANAGED = "MANAGED"
    STARTING = "STARTING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    CANCELING = "CANCELING"
    CANCELED = "CANCELED"


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


@whitelist_for_serdes
class PipelineRunStatsSnapshot(
    namedtuple(
        "_PipelineRunStatsSnapshot",
        (
            "run_id steps_succeeded steps_failed materializations "
            "expectations enqueued_time launch_time start_time end_time"
        ),
    )
):
    def __new__(
        cls,
        run_id,
        steps_succeeded,
        steps_failed,
        materializations,
        expectations,
        enqueued_time,
        launch_time,
        start_time,
        end_time,
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


class PipelineRunSerializer(DefaultNamedTupleSerializer):
    @classmethod
    def value_from_storage_dict(cls, storage_dict, _klass):
        # called by the serdes layer, delegates to helper method with expanded kwargs
        return pipeline_run_from_storage(**storage_dict)


def pipeline_run_from_storage(
    pipeline_name=None,
    run_id=None,
    run_config=None,
    mode=None,
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

    return PipelineRun(  # pylint: disable=redundant-keyword-arg
        pipeline_name=pipeline_name,
        run_id=run_id,
        run_config=run_config,
        mode=mode,
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
    )


@whitelist_for_serdes(serializer=PipelineRunSerializer)
class PipelineRun(
    namedtuple(
        "_PipelineRun",
        (
            "pipeline_name run_id run_config mode solid_selection solids_to_execute "
            "step_keys_to_execute status tags root_run_id parent_run_id "
            "pipeline_snapshot_id execution_plan_snapshot_id external_pipeline_origin"
        ),
    )
):
    """Serializable internal representation of a pipeline run, as stored in a
    :py:class:`~dagster.core.storage.runs.RunStorage`.
    """

    def __new__(
        cls,
        pipeline_name=None,
        run_id=None,
        run_config=None,
        mode=None,
        solid_selection=None,
        solids_to_execute=None,
        step_keys_to_execute=None,
        status=None,
        tags=None,
        root_run_id=None,
        parent_run_id=None,
        pipeline_snapshot_id=None,
        execution_plan_snapshot_id=None,
        external_pipeline_origin=None,
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
        check.opt_set_param(solids_to_execute, "solids_to_execute", of_type=str)
        # a list of solid queries provided by the user
        # possible to be None when only solids_to_execute is set by the user directly
        check.opt_list_param(solid_selection, "solid_selection", of_type=str)
        check.opt_list_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)

        # Placing this with the other imports causes a cyclic import
        # https://github.com/dagster-io/dagster/issues/3181
        from dagster.core.host_representation.origin import ExternalPipelineOrigin

        if status == PipelineRunStatus.QUEUED:
            check.inst_param(
                external_pipeline_origin,
                "external_pipeline_origin",
                ExternalPipelineOrigin,
                "external_pipeline_origin is required for queued runs",
            )

        return super(PipelineRun, cls).__new__(
            cls,
            pipeline_name=check.opt_str_param(pipeline_name, "pipeline_name"),
            run_id=check.opt_str_param(run_id, "run_id", default=make_new_run_id()),
            run_config=check.opt_dict_param(run_config, "run_config", key_type=str),
            mode=check.opt_str_param(mode, "mode"),
            solid_selection=solid_selection,
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
        )

    def with_status(self, status):
        if status == PipelineRunStatus.QUEUED:
            # Placing this with the other imports causes a cyclic import
            # https://github.com/dagster-io/dagster/issues/3181
            from dagster.core.host_representation.origin import ExternalPipelineOrigin

            check.inst(
                self.external_pipeline_origin,
                ExternalPipelineOrigin,
                "external_pipeline_origin is required for queued runs",
            )

        return self._replace(status=status)

    def with_mode(self, mode):
        return self._replace(mode=mode)

    def with_tags(self, tags):
        return self._replace(tags=tags)

    def get_root_run_id(self):
        return self.tags.get(ROOT_RUN_ID_TAG)

    def get_parent_run_id(self):
        return self.tags.get(PARENT_RUN_ID_TAG)

    @property
    def is_finished(self):
        return (
            self.status == PipelineRunStatus.SUCCESS
            or self.status == PipelineRunStatus.FAILURE
            or self.status == PipelineRunStatus.CANCELED
        )

    @property
    def is_success(self):
        return self.status == PipelineRunStatus.SUCCESS

    @property
    def is_failure(self):
        return self.status == PipelineRunStatus.FAILURE or self.status == PipelineRunStatus.CANCELED

    @property
    def is_resume_retry(self):
        return self.tags.get(RESUME_RETRY_TAG) == "true"

    @property
    def previous_run_id(self):
        # Compat
        return self.parent_run_id

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


@whitelist_for_serdes
class PipelineRunsFilter(
    namedtuple("_PipelineRunsFilter", "run_ids pipeline_name statuses tags snapshot_id")
):
    def __new__(cls, run_ids=None, pipeline_name=None, statuses=None, tags=None, snapshot_id=None):
        return super(PipelineRunsFilter, cls).__new__(
            cls,
            run_ids=check.opt_list_param(run_ids, "run_ids", of_type=str),
            pipeline_name=check.opt_str_param(pipeline_name, "pipeline_name"),
            statuses=check.opt_list_param(statuses, "statuses", of_type=PipelineRunStatus),
            tags=check.opt_dict_param(tags, "tags", key_type=str, value_type=str),
            snapshot_id=check.opt_str_param(snapshot_id, "snapshot_id"),
        )

    @staticmethod
    def for_schedule(schedule):
        return PipelineRunsFilter(tags=PipelineRun.tags_for_schedule(schedule))

    @staticmethod
    def for_partition(partition_set, partition):
        return PipelineRunsFilter(tags=PipelineRun.tags_for_partition_set(partition_set, partition))

    @staticmethod
    def for_sensor(sensor):
        return PipelineRunsFilter(tags=PipelineRun.tags_for_sensor(sensor))

    @staticmethod
    def for_backfill(backfill_id):
        return PipelineRunsFilter(tags=PipelineRun.tags_for_backfill_id(backfill_id))


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
class ExecutionSelector(namedtuple("_ExecutionSelector", "name solid_subset")):
    """
    Kept here to maintain loading of PipelineRuns from when it was still alive.
    """

    def __new__(cls, name, solid_subset=None):
        return super(ExecutionSelector, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            solid_subset=None
            if solid_subset is None
            else check.list_param(solid_subset, "solid_subset", of_type=str),
        )
