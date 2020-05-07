from collections import namedtuple
from enum import Enum

from dagster import check
from dagster.core.execution.config import IRunConfig
from dagster.core.utils import make_new_run_id
from dagster.serdes import whitelist_for_serdes

from .tags import (
    BACKFILL_ID_TAG,
    PARTITION_NAME_TAG,
    PARTITION_SET_TAG,
    RESUME_RETRY_TAG,
    SCHEDULE_NAME_TAG,
)


@whitelist_for_serdes
class PipelineRunStatus(Enum):
    NOT_STARTED = 'NOT_STARTED'
    MANAGED = 'MANAGED'
    STARTED = 'STARTED'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'


@whitelist_for_serdes
class PipelineRunStatsSnapshot(
    namedtuple(
        '_PipelineRunStatsSnapshot',
        (
            'run_id steps_succeeded steps_failed materializations '
            'expectations start_time end_time'
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
        start_time,
        end_time,
    ):
        return super(PipelineRunStatsSnapshot, cls).__new__(
            cls,
            run_id=check.str_param(run_id, 'run_id'),
            steps_succeeded=check.int_param(steps_succeeded, 'steps_succeeded'),
            steps_failed=check.int_param(steps_failed, 'steps_failed'),
            materializations=check.int_param(materializations, 'materializations'),
            expectations=check.int_param(expectations, 'expectations'),
            start_time=check.opt_float_param(start_time, 'start_time'),
            end_time=check.opt_float_param(end_time, 'end_time'),
        )


@whitelist_for_serdes
class PipelineRun(
    namedtuple(
        '_PipelineRun',
        (
            'pipeline_name run_id environment_dict mode solid_subset '
            'step_keys_to_execute status tags root_run_id parent_run_id '
            'pipeline_snapshot_id execution_plan_snapshot_id'
        ),
    ),
    IRunConfig,
):
    '''Serializable internal representation of a pipeline run, as stored in a
    :py:class:`~dagster.core.storage.runs.RunStorage`.
    '''

    # serdes log
    # * removed reexecution_config - serdes logic expected to strip unknown keys so no need to preserve
    # * added pipeline_snapshot_id
    # * renamed previous_run_id -> parent_run_id, added root_run_id
    #   serdes will set parent_run_id = root_run_id = previous_run_id when __new__ is called with
    #   a record that has previous_run_id set but neither of the new fields, i.e., when
    #   deserializing an old record; the old field will then be dropped when serialized back to
    #   storage
    # * added execution_plan_snapshot_id
    # * removed selector
    # * added solid_subset
    def __new__(
        cls,
        pipeline_name=None,
        run_id=None,
        environment_dict=None,
        mode=None,
        solid_subset=None,
        step_keys_to_execute=None,
        status=None,
        tags=None,
        root_run_id=None,
        parent_run_id=None,
        pipeline_snapshot_id=None,
        execution_plan_snapshot_id=None,
        ## GRAVEYARD BELOW
        # see https://github.com/dagster-io/dagster/issues/2372 for explanation
        previous_run_id=None,
        selector=None,
    ):
        from dagster.core.definitions.pipeline import ExecutionSelector

        check.opt_list_param(solid_subset, 'solid_subset', of_type=str)
        check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

        check.opt_str_param(root_run_id, 'root_run_id')
        check.opt_str_param(parent_run_id, 'parent_run_id')

        check.invariant(
            (root_run_id is not None and parent_run_id is not None)
            or (root_run_id is None and parent_run_id is None),
            (
                'Must set both root_run_id and parent_run_id when creating a PipelineRun that '
                'belongs to a run group'
            ),
        )

        # Compatibility
        # ----------------------------------------------------------------------------------------
        # Historical runs may have previous_run_id set, in which case
        # that previous ID becomes both the root and the parent
        if previous_run_id:
            if not (parent_run_id and root_run_id):
                parent_run_id = previous_run_id
                root_run_id = previous_run_id

        check.opt_inst_param(selector, 'selector', ExecutionSelector)
        if selector:
            check.invariant(
                pipeline_name is None or selector.name == pipeline_name,
                (
                    'Conflicting pipeline name {pipeline_name} in arguments to PipelineRun: '
                    'selector was passed with pipeline {selector_pipeline}'.format(
                        pipeline_name=pipeline_name, selector_pipeline=selector.name
                    )
                ),
            )
            if pipeline_name is None:
                pipeline_name = selector.name

            check.invariant(
                solid_subset is None or selector.solid_subset == solid_subset,
                (
                    'Conflicting solid_subset {solid_subset} in arguments to PipelineRun: '
                    'selector was passed with subset {selector_subset}'.format(
                        solid_subset=solid_subset, selector_subset=selector.solid_subset
                    )
                ),
            )
            if solid_subset is None:
                solid_subset = selector.solid_subset
        # ----------------------------------------------------------------------------------------

        return super(PipelineRun, cls).__new__(
            cls,
            pipeline_name=check.opt_str_param(pipeline_name, 'pipeline_name'),
            run_id=check.opt_str_param(run_id, 'run_id', default=make_new_run_id()),
            environment_dict=check.opt_dict_param(
                environment_dict, 'environment_dict', key_type=str
            ),
            mode=check.opt_str_param(mode, 'mode'),
            solid_subset=solid_subset,
            step_keys_to_execute=step_keys_to_execute,
            status=check.opt_inst_param(
                status, 'status', PipelineRunStatus, PipelineRunStatus.NOT_STARTED
            ),
            tags=check.opt_dict_param(tags, 'tags', key_type=str),
            root_run_id=root_run_id,
            parent_run_id=parent_run_id,
            pipeline_snapshot_id=check.opt_str_param(pipeline_snapshot_id, 'pipeline_snapshot_id'),
            execution_plan_snapshot_id=check.opt_str_param(
                execution_plan_snapshot_id, 'execution_plan_snapshot_id'
            ),
        )

    def with_status(self, status):
        return self._replace(status=status)

    def with_mode(self, mode):
        return self._replace(mode=mode)

    def with_tags(self, tags):
        return self._replace(tags=tags)

    def with_pipeline_snapshot_id(self, pipeline_snapshot_id):
        return self._replace(pipeline_snapshot_id=pipeline_snapshot_id)

    def with_execution_plan_snapshot_id(self, execution_plan_snapshot_id):
        return self._replace(execution_plan_snapshot_id=execution_plan_snapshot_id)

    @property
    def is_finished(self):
        return self.status == PipelineRunStatus.SUCCESS or self.status == PipelineRunStatus.FAILURE

    @property
    def is_resume_retry(self):
        return self.tags.get(RESUME_RETRY_TAG) == 'true'

    @property
    def selector(self):
        from dagster.core.definitions.pipeline import ExecutionSelector

        return ExecutionSelector(name=self.pipeline_name, solid_subset=self.solid_subset)

    @property
    def previous_run_id(self):
        # Compat
        return self.parent_run_id

    @staticmethod
    def tags_for_schedule(schedule):
        return {SCHEDULE_NAME_TAG: schedule.name}

    @staticmethod
    def tags_for_backfill_id(backfill_id):
        return {BACKFILL_ID_TAG: backfill_id}

    @staticmethod
    def tags_for_partition_set(partition_set, partition):
        return {PARTITION_NAME_TAG: partition.name, PARTITION_SET_TAG: partition_set.name}


@whitelist_for_serdes
class PipelineRunsFilter(namedtuple('_PipelineRunsFilter', 'run_ids pipeline_name status tags')):
    def __new__(
        cls, run_ids=None, pipeline_name=None, status=None, tags=None,
    ):
        run_ids = check.opt_list_param(run_ids, 'run_ids', of_type=str)
        return super(PipelineRunsFilter, cls).__new__(
            cls,
            run_ids=run_ids,
            pipeline_name=check.opt_str_param(pipeline_name, 'pipeline_name'),
            status=status,
            tags=check.opt_dict_param(tags, 'tags', key_type=str, value_type=str),
        )

    @staticmethod
    def for_schedule(schedule):
        return PipelineRunsFilter(tags=PipelineRun.tags_for_schedule(schedule))

    @staticmethod
    def for_partition(partition_set, partition):
        return PipelineRunsFilter(tags=PipelineRun.tags_for_partition_set(partition_set, partition))
