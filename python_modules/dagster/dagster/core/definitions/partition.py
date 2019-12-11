from abc import ABCMeta, abstractmethod
from collections import namedtuple

import six

from dagster import check
from dagster.core.definitions.schedule import ScheduleDefinition
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster.utils import merge_dicts


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


class IPartitionSelector(six.with_metaclass(ABCMeta)):  # pylint: disable=no-init
    '''
    Interface for a strategy of selecting a partition for a given pipeline
    '''

    @abstractmethod
    def select_partition(self, partition_set_def):
        pass


class SortedPartitionSelector(IPartitionSelector):
    def __init__(self, sort_key_fn=None, reverse=False):
        self._sort_key_fn = check.opt_callable_param(sort_key_fn, 'sort_key_fn', default=by_name)
        self._reverse = check.bool_param(reverse, 'reverse')

    def select_partition(self, partition_set_def):

        partition_set_def = check.inst_param(
            partition_set_def, 'partition_set_def', PartitionSetDefinition
        )

        partitions = partition_set_def.get_partitions()
        if not partitions:
            raise DagsterInvalidDefinitionError(
                'Tried to select partition from an empty partition set.'
            )
        sorted_partitions = sorted(partitions, key=self._sort_key_fn, reverse=self._reverse)
        return sorted_partitions[-1]


class LastPartitionSelector(SortedPartitionSelector):
    def __init__(self, sort_key_fn=None):
        super(LastPartitionSelector, self).__init__(sort_key_fn=sort_key_fn, reverse=False)


class FirstPartitionSelector(SortedPartitionSelector):
    def __init__(self, sort_key_fn=None):
        super(FirstPartitionSelector, self).__init__(sort_key_fn=sort_key_fn, reverse=True)


class PartitionSetDefinition(
    namedtuple(
        '_PartitionSetDefinition',
        (
            'name pipeline_name partition_fn user_defined_environment_dict_fn_for_partition user_defined_tags_fn_for_partition'
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
        partition_selector=LastPartitionSelector(),
        environment_vars=None,
    ):
        '''Create a ScheduleDefinition from a PartitionSetDefinition

        Arguments:
            schedule_name (str): The name of the schedule.
            cron_schedule (str): A valid cron string for the schedule
            partition_selector (IPartitionSelector): A partition selector for the schedule
            environment_vars (Optional[dict]): The environment variables to set for the schedule

        Returns:
            ScheduleDefinition -- The generated ScheduleDefinition for the IPartitionSelector
        '''

        check.inst_param(partition_selector, 'partition_selector', IPartitionSelector)

        def _environment_dict_fn_wrapper():
            selected_partition = partition_selector.select_partition(partition_set_def=self)
            if not selected_partition:
                raise DagsterInvariantViolationError(
                    "PartitionSelector {selector} did not return "
                    "a partition from PartitionSet {partition_set}".format(
                        selector=partition_selector.__class__.__name__, partition_set=self.name
                    )
                )

            return self.environment_dict_for_partition(selected_partition)

        def _tags_fn_wrapper():
            selected_partition = partition_selector.select_partition(partition_set_def=self)
            if not selected_partition:
                raise DagsterInvariantViolationError(
                    "PartitionSelector {selector} did not return "
                    "a partition from PartitionSet {partition_set}".format(
                        selector=partition_selector.__class__.__name__, partition_set=self.name
                    )
                )

            return self.tags_for_partition(selected_partition)

        return ScheduleDefinition(
            name=schedule_name,
            cron_schedule=cron_schedule,
            pipeline_name=self.pipeline_name,
            environment_dict_fn=_environment_dict_fn_wrapper,
            tags_fn=_tags_fn_wrapper,
            environment_vars=environment_vars,
        )


class RepositoryPartitionsHandle(namedtuple('_RepositoryPartitionsHandle', ('partition_set_defs'))):
    def __new__(cls, partition_set_defs):
        return super(RepositoryPartitionsHandle, cls).__new__(
            cls,
            partition_set_defs=check.list_param(
                partition_set_defs, 'partition_set_defs', PartitionSetDefinition
            ),
        )

    def get_all_partition_sets(self):
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
