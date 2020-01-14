from collections import namedtuple

from dagster import check
from dagster.core.definitions.pipeline import PipelineRunsFilter
from dagster.core.definitions.schedule import ScheduleDefinition, ScheduleExecutionContext
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.utils import merge_dicts

from .mode import DEFAULT_MODE_NAME


def by_name(partition):
    return partition.name


class Partition(namedtuple('_Partition', ('value name'))):
    '''
    Partition is the representation of a logical slice across an axis of a pipeline's work

    Args:
        partition (Any): The object for this partition
        name (str): Name for this partition
    '''

    def __new__(cls, value=None, name=None):
        return super(Partition, cls).__new__(
            cls, name=check.opt_str_param(name, 'name', str(value)), value=value
        )


def last_partition(context, partition_set_def):
    check.inst_param(context, 'context', ScheduleExecutionContext)
    partition_set_def = check.inst_param(
        partition_set_def, 'partition_set_def', PartitionSetDefinition
    )

    partitions = partition_set_def.get_partitions()
    if not partitions:
        return None
    return partitions[-1]


def last_empty_partition(context, partition_set_def):
    check.inst_param(context, 'context', ScheduleExecutionContext)
    partition_set_def = check.inst_param(
        partition_set_def, 'partition_set_def', PartitionSetDefinition
    )
    partitions = partition_set_def.get_partitions()
    if not partitions:
        return None
    selected = None
    for partition in reversed(partitions):
        filters = PipelineRunsFilter(
            tags={
                "dagster/partition": partition.name,
                'dagster/partition_set': partition_set_def.name,
            }
        )
        matching = context.instance.get_runs(filters)
        if not any(run.status == PipelineRunStatus.SUCCESS for run in matching):
            selected = partition
            break
    return selected


def first_partition(context, partition_set_def=None):
    check.inst_param(context, 'context', ScheduleExecutionContext)
    partition_set_def = check.inst_param(
        partition_set_def, 'partition_set_def', PartitionSetDefinition
    )

    partitions = partition_set_def.get_partitions()
    if not partitions:
        return None

    return partitions[0]


class PartitionSetDefinition(
    namedtuple(
        '_PartitionSetDefinition',
        (
            'name pipeline_name partition_fn solid_subset mode user_defined_environment_dict_fn_for_partition user_defined_tags_fn_for_partition'
        ),
    )
):
    '''
    Defines a partition set, representing the set of slices making up an axis of a pipeline

    Args:
        name (str): Name for this partition set
        pipeline_name (str): The name of the pipeline definition
        partition_fn (Callable[void, List[Partition]]): User-provided function to define the set of
            valid partition objects.
        solid_subset (Optional[List[str]]): The list of names of solid invocations (i.e., of
            unaliased solids or of their aliases if aliased) to execute with this partition.
        mode (Optional[str]): The mode to apply when executing this partition. (default: 'default')
        environment_dict_fn_for_partition (Callable[[Partition], [Dict]]): A
            function that takes a Partition and returns the environment
            configuration that parameterizes the execution for this partition, as a dict
        tags_fn_for_partition (Callable[[Partition], Optional[dict[str, str]]]): A function that
            takes a Partition and returns a list of key value pairs that will be
            added to the generated run for this partition.
    '''

    def __new__(
        cls,
        name,
        pipeline_name,
        partition_fn,
        solid_subset=None,
        mode=None,
        environment_dict_fn_for_partition=lambda _partition: {},
        tags_fn_for_partition=lambda _partition: {},
    ):
        def _wrap(x):
            if isinstance(x, Partition):
                return x
            if isinstance(x, str):
                return Partition(x)
            raise DagsterInvalidDefinitionError(
                'Expected <Partition> | <str>, received {type}'.format(type=type(x))
            )

        return super(PartitionSetDefinition, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            pipeline_name=check.str_param(pipeline_name, 'pipeline_name'),
            partition_fn=lambda: [
                _wrap(x) for x in check.callable_param(partition_fn, 'partition_fn')()
            ],
            solid_subset=check.opt_nullable_list_param(solid_subset, 'solid_subset', of_type=str),
            mode=check.opt_str_param(mode, 'mode', DEFAULT_MODE_NAME),
            user_defined_environment_dict_fn_for_partition=check.callable_param(
                environment_dict_fn_for_partition, 'environment_dict_fn_for_partition'
            ),
            user_defined_tags_fn_for_partition=check.callable_param(
                tags_fn_for_partition, 'tags_fn_for_partition'
            ),
        )

    def environment_dict_for_partition(self, partition):
        return self.user_defined_environment_dict_fn_for_partition(partition)

    def tags_for_partition(self, partition):
        user_tags = self.user_defined_tags_fn_for_partition(partition)
        # TODO: Validate tags from user - Check they returned a Dict[str, str]
        check.invariant('dagster/partition' not in user_tags)
        check.invariant('dagster/partition_set' not in user_tags)
        return merge_dicts(
            {'dagster/partition': partition.name, 'dagster/partition_set': self.name}, user_tags
        )

    def get_partitions(self):
        return self.partition_fn()

    def create_schedule_definition(
        self,
        schedule_name,
        cron_schedule,
        should_execute=None,
        partition_selector=last_partition,
        environment_vars=None,
    ):
        '''Create a ScheduleDefinition from a PartitionSetDefinition.

        Arguments:
            schedule_name (str): The name of the schedule.
            cron_schedule (str): A valid cron string for the schedule
            should_execute (Optional[function]): Function that runs at schedule execution time that
            determines whether a schedule should execute. Defaults to a function that always returns
            ``True``.
            partition_selector (Callable[PartitionSet], Partition): A partition selector for the
                schedule
            environment_vars (Optional[dict]): The environment variables to set for the schedule

        Returns:
            ScheduleDefinition -- The generated ScheduleDefinition for the partition selector
        '''

        check.str_param(schedule_name, 'schedule_name')
        check.str_param(cron_schedule, 'cron_schedule')
        check.opt_callable_param(should_execute, 'should_execute')
        check.opt_dict_param(environment_vars, 'environment_vars', key_type=str, value_type=str)
        check.callable_param(partition_selector, 'partition_selector')

        def _should_execute_wrapper(context):
            check.inst_param(context, 'context', ScheduleExecutionContext)
            selected_partition = partition_selector(context, self)
            if not selected_partition:
                return False
            elif not should_execute:
                return True
            else:
                return should_execute(context)

        def _environment_dict_fn_wrapper(context):
            check.inst_param(context, 'context', ScheduleExecutionContext)
            selected_partition = partition_selector(context, self)
            if not selected_partition:
                raise DagsterInvariantViolationError(
                    "The partition selection function `{selector}` did not return "
                    "a partition from PartitionSet {partition_set}".format(
                        selector=getattr(partition_selector, '__name__', repr(partition_selector)),
                        partition_set=self.name,
                    )
                )

            return self.environment_dict_for_partition(selected_partition)

        def _tags_fn_wrapper(context):
            check.inst_param(context, 'context', ScheduleExecutionContext)
            selected_partition = partition_selector(context, self)
            if not selected_partition:
                raise DagsterInvariantViolationError(
                    "The partition selection function `{selector}` did not return "
                    "a partition from PartitionSet {partition_set}".format(
                        selector=getattr(partition_selector, '__name__', repr(partition_selector)),
                        partition_set=self.name,
                    )
                )

            return self.tags_for_partition(selected_partition)

        return PartitionScheduleDefinition(
            name=schedule_name,
            cron_schedule=cron_schedule,
            pipeline_name=self.pipeline_name,
            environment_dict_fn=_environment_dict_fn_wrapper,
            tags_fn=_tags_fn_wrapper,
            solid_subset=self.solid_subset,
            mode=self.mode,
            should_execute=_should_execute_wrapper,
            environment_vars=environment_vars,
            partition_set=self,
        )


class PartitionScheduleDefinition(ScheduleDefinition):
    __slots__ = ['_partition_set']

    def __init__(
        self,
        name,
        cron_schedule,
        pipeline_name,
        environment_dict_fn,
        tags_fn,
        solid_subset,
        mode,
        should_execute,
        environment_vars,
        partition_set,
    ):
        super(PartitionScheduleDefinition, self).__init__(
            name=name,
            cron_schedule=cron_schedule,
            pipeline_name=pipeline_name,
            environment_dict_fn=environment_dict_fn,
            tags_fn=tags_fn,
            solid_subset=solid_subset,
            mode=mode,
            should_execute=should_execute,
            environment_vars=environment_vars,
        )
        self._partition_set = check.inst_param(
            partition_set, 'partition_set', PartitionSetDefinition
        )

    def get_partition_set(self):
        return self._partition_set


class RepositoryPartitionsHandle(namedtuple('_RepositoryPartitionsHandle', ('partition_set_defs'))):
    def __new__(cls, partition_set_defs):
        return super(RepositoryPartitionsHandle, cls).__new__(
            cls,
            partition_set_defs=check.list_param(
                partition_set_defs, 'partition_set_defs', PartitionSetDefinition
            ),
        )

    def get_partition_sets(self):
        return self.partition_set_defs

    def get_partition_set(self, name):
        return next(
            iter(
                _partition_set
                for _partition_set in self.partition_set_defs
                if _partition_set.name == name
            ),
            None,
        )


def repository_partitions(arg=None):
    ''' Decorator to define the set of partition sets for a repository '''
    if callable(arg):
        return RepositoryPartitionsHandle(partition_set_defs=arg())

    def _wrap(fn):
        return RepositoryPartitionsHandle(partition_set_defs=fn())

    return _wrap
