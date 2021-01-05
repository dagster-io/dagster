from collections import namedtuple

from dagster import check
from dagster.core.definitions.schedule import ScheduleDefinition, ScheduleExecutionContext
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus, PipelineRunsFilter
from dagster.core.storage.tags import check_tags
from dagster.utils import merge_dicts

from .mode import DEFAULT_MODE_NAME
from .utils import check_valid_name


def by_name(partition):
    return partition.name


class Partition(namedtuple("_Partition", ("value name"))):
    """
    Partition is the representation of a logical slice across an axis of a pipeline's work

    Args:
        value (Any): The object for this partition
        name (str): Name for this partition
    """

    def __new__(cls, value=None, name=None):
        return super(Partition, cls).__new__(
            cls, name=check.opt_str_param(name, "name", str(value)), value=value
        )


def last_empty_partition(context, partition_set_def):
    check.inst_param(context, "context", ScheduleExecutionContext)
    partition_set_def = check.inst_param(
        partition_set_def, "partition_set_def", PartitionSetDefinition
    )
    partitions = partition_set_def.get_partitions()
    if not partitions:
        return None
    selected = None
    for partition in reversed(partitions):
        filters = PipelineRunsFilter.for_partition(partition_set_def, partition)
        matching = context.instance.get_runs(filters)
        if not any(run.status == PipelineRunStatus.SUCCESS for run in matching):
            selected = partition
            break
    return selected


def first_partition(context, partition_set_def=None):
    check.inst_param(context, "context", ScheduleExecutionContext)
    partition_set_def = check.inst_param(
        partition_set_def, "partition_set_def", PartitionSetDefinition
    )

    partitions = partition_set_def.get_partitions()
    if not partitions:
        return None

    return partitions[0]


class PartitionSetDefinition(
    namedtuple(
        "_PartitionSetDefinition",
        (
            "name pipeline_name partition_fn solid_selection mode "
            "user_defined_run_config_fn_for_partition user_defined_tags_fn_for_partition"
        ),
    )
):
    """
    Defines a partition set, representing the set of slices making up an axis of a pipeline

    Args:
        name (str): Name for this partition set
        pipeline_name (str): The name of the pipeline definition
        partition_fn (Callable[void, List[Partition]]): User-provided function to define the set of
            valid partition objects.
        solid_selection (Optional[List[str]]): A list of solid subselection (including single
            solid names) to execute with this partition. e.g. ``['*some_solid+', 'other_solid']``
        mode (Optional[str]): The mode to apply when executing this partition. (default: 'default')
        run_config_fn_for_partition (Callable[[Partition], [Dict]]): A
            function that takes a :py:class:`~dagster.Partition` and returns the run
            configuration that parameterizes the execution for this partition, as a dict
        tags_fn_for_partition (Callable[[Partition], Optional[dict[str, str]]]): A function that
            takes a :py:class:`~dagster.Partition` and returns a list of key value pairs that will
            be added to the generated run for this partition.
    """

    def __new__(
        cls,
        name,
        pipeline_name,
        partition_fn,
        solid_selection=None,
        mode=None,
        run_config_fn_for_partition=lambda _partition: {},
        tags_fn_for_partition=lambda _partition: {},
    ):
        def _wrap(x):
            if isinstance(x, Partition):
                return x
            if isinstance(x, str):
                return Partition(x)
            raise DagsterInvalidDefinitionError(
                "Expected <Partition> | <str>, received {type}".format(type=type(x))
            )

        return super(PartitionSetDefinition, cls).__new__(
            cls,
            name=check_valid_name(name),
            pipeline_name=check.str_param(pipeline_name, "pipeline_name"),
            partition_fn=lambda: [
                _wrap(x) for x in check.callable_param(partition_fn, "partition_fn")()
            ],
            solid_selection=check.opt_nullable_list_param(
                solid_selection, "solid_selection", of_type=str
            ),
            mode=check.opt_str_param(mode, "mode", DEFAULT_MODE_NAME),
            user_defined_run_config_fn_for_partition=check.callable_param(
                run_config_fn_for_partition, "run_config_fn_for_partition"
            ),
            user_defined_tags_fn_for_partition=check.callable_param(
                tags_fn_for_partition, "tags_fn_for_partition"
            ),
        )

    def run_config_for_partition(self, partition):
        return self.user_defined_run_config_fn_for_partition(partition)

    def tags_for_partition(self, partition):
        user_tags = self.user_defined_tags_fn_for_partition(partition)
        check_tags(user_tags, "user_tags")

        tags = merge_dicts(user_tags, PipelineRun.tags_for_partition_set(self, partition))

        return tags

    def get_partitions(self):
        return self.partition_fn()

    def get_partition(self, name):
        for partition in self.get_partitions():
            if partition.name == name:
                return partition

        check.failed("Partition name {} not found!".format(name))

    def get_partition_names(self):
        return [part.name for part in self.get_partitions()]

    def create_schedule_definition(
        self,
        schedule_name,
        cron_schedule,
        partition_selector,
        should_execute=None,
        environment_vars=None,
        execution_timezone=None,
    ):
        """Create a ScheduleDefinition from a PartitionSetDefinition.

        Arguments:
            schedule_name (str): The name of the schedule.
            cron_schedule (str): A valid cron string for the schedule
            partition_selector (Callable[ScheduleExecutionContext, PartitionSetDefinition],
            Partition): Function that determines the partition to use at a given execution time.
            For time-based partition sets, will likely be either `identity_partition_selector` or a
            selector returned by `create_offset_partition_selector`.
            should_execute (Optional[function]): Function that runs at schedule execution time that
            determines whether a schedule should execute. Defaults to a function that always returns
            ``True``.
            environment_vars (Optional[dict]): The environment variables to set for the schedule.
            execution_timezone (Optional[str]): Timezone in which the schedule should run. Only works
                with DagsterDaemonScheduler, and must be set when using that scheduler.

        Returns:
            ScheduleDefinition: The generated ScheduleDefinition for the partition selector
        """

        check.str_param(schedule_name, "schedule_name")
        check.str_param(cron_schedule, "cron_schedule")
        check.opt_callable_param(should_execute, "should_execute")
        check.opt_dict_param(environment_vars, "environment_vars", key_type=str, value_type=str)
        check.callable_param(partition_selector, "partition_selector")
        check.opt_str_param(execution_timezone, "execution_timezone")

        def _should_execute_wrapper(context):
            check.inst_param(context, "context", ScheduleExecutionContext)
            selected_partition = partition_selector(context, self)

            if not selected_partition or not selected_partition.name in self.get_partition_names():
                return False
            elif not should_execute:
                return True
            else:
                return should_execute(context)

        def _run_config_fn_wrapper(context):
            check.inst_param(context, "context", ScheduleExecutionContext)
            selected_partition = partition_selector(context, self)
            if not selected_partition or not selected_partition.name in self.get_partition_names():
                raise DagsterInvariantViolationError(
                    "The partition selection function `{selector}` did not return "
                    "a partition from PartitionSet {partition_set}".format(
                        selector=getattr(partition_selector, "__name__", repr(partition_selector)),
                        partition_set=self.name,
                    )
                )

            return self.run_config_for_partition(selected_partition)

        def _tags_fn_wrapper(context):
            check.inst_param(context, "context", ScheduleExecutionContext)
            selected_partition = partition_selector(context, self)
            if not selected_partition:
                raise DagsterInvariantViolationError(
                    "The partition selection function `{selector}` did not return "
                    "a partition from PartitionSet {partition_set}".format(
                        selector=getattr(partition_selector, "__name__", repr(partition_selector)),
                        partition_set=self.name,
                    )
                )

            return self.tags_for_partition(selected_partition)

        return PartitionScheduleDefinition(
            name=schedule_name,
            cron_schedule=cron_schedule,
            pipeline_name=self.pipeline_name,
            run_config_fn=_run_config_fn_wrapper,
            tags_fn=_tags_fn_wrapper,
            solid_selection=self.solid_selection,
            mode=self.mode,
            should_execute=_should_execute_wrapper,
            environment_vars=environment_vars,
            partition_set=self,
            execution_timezone=execution_timezone,
        )


class PartitionScheduleDefinition(ScheduleDefinition):
    __slots__ = ["_partition_set"]

    def __init__(
        self,
        name,
        cron_schedule,
        pipeline_name,
        tags_fn,
        solid_selection,
        mode,
        should_execute,
        environment_vars,
        partition_set,
        run_config_fn=None,
        execution_timezone=None,
    ):
        super(PartitionScheduleDefinition, self).__init__(
            name=check_valid_name(name),
            cron_schedule=cron_schedule,
            pipeline_name=pipeline_name,
            run_config_fn=run_config_fn,
            tags_fn=tags_fn,
            solid_selection=solid_selection,
            mode=mode,
            should_execute=should_execute,
            environment_vars=environment_vars,
            execution_timezone=execution_timezone,
        )
        self._partition_set = check.inst_param(
            partition_set, "partition_set", PartitionSetDefinition
        )

    def get_partition_set(self):
        return self._partition_set
