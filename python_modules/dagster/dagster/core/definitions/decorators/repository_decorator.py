from functools import update_wrapper
from typing import Any, Callable, Optional, Union, overload

import dagster._check as check
from dagster.core.errors import DagsterInvalidDefinitionError

from ..graph_definition import GraphDefinition
from ..partition import PartitionSetDefinition
from ..pipeline_definition import PipelineDefinition
from ..repository_definition import (
    VALID_REPOSITORY_DATA_DICT_KEYS,
    CachingRepositoryData,
    RepositoryData,
    RepositoryDefinition,
)
from ..schedule_definition import ScheduleDefinition
from ..sensor_definition import SensorDefinition


class _Repository:
    def __init__(self, name: Optional[str] = None, description: Optional[str] = None):
        self.name = check.opt_str_param(name, "name")
        self.description = check.opt_str_param(description, "description")

    def __call__(self, fn: Callable[[], Any]) -> RepositoryDefinition:
        from dagster.core.asset_defs import AssetGroup

        check.callable_param(fn, "fn")

        if not self.name:
            self.name = fn.__name__

        repository_definitions = fn()

        repository_data: Union[CachingRepositoryData, RepositoryData]
        if isinstance(repository_definitions, list):
            bad_definitions = []
            for i, definition in enumerate(repository_definitions):
                if not (
                    isinstance(definition, PipelineDefinition)
                    or isinstance(definition, PartitionSetDefinition)
                    or isinstance(definition, ScheduleDefinition)
                    or isinstance(definition, SensorDefinition)
                    or isinstance(definition, GraphDefinition)
                    or isinstance(definition, AssetGroup)
                ):
                    bad_definitions.append((i, type(definition)))
            if bad_definitions:
                bad_definitions_str = ", ".join(
                    [
                        "value of type {type_} at index {i}".format(type_=type_, i=i)
                        for i, type_ in bad_definitions
                    ]
                )
                raise DagsterInvalidDefinitionError(
                    "Bad return value from repository construction function: all elements of list "
                    "must be of type JobDefinition, GraphDefinition, PipelineDefinition, "
                    "PartitionSetDefinition, ScheduleDefinition, or SensorDefinition. "
                    f"Got {bad_definitions_str}."
                )
            repository_data = CachingRepositoryData.from_list(repository_definitions)

        elif isinstance(repository_definitions, dict):
            if not set(repository_definitions.keys()).issubset(VALID_REPOSITORY_DATA_DICT_KEYS):
                raise DagsterInvalidDefinitionError(
                    "Bad return value from repository construction function: dict must not contain "
                    "keys other than {{'pipelines', 'partition_sets', 'schedules', 'jobs'}}: found "
                    "{bad_keys}".format(
                        bad_keys=", ".join(
                            [
                                "'{key}'".format(key=key)
                                for key in repository_definitions.keys()
                                if key not in VALID_REPOSITORY_DATA_DICT_KEYS
                            ]
                        )
                    )
                )
            repository_data = CachingRepositoryData.from_dict(repository_definitions)
        elif isinstance(repository_definitions, RepositoryData):
            repository_data = repository_definitions
        else:
            raise DagsterInvalidDefinitionError(
                "Bad return value of type {type_} from repository construction function: must "
                "return list, dict, or RepositoryData. See the @repository decorator docstring for "
                "details and examples".format(type_=type(repository_definitions)),
            )

        repository_def = RepositoryDefinition(
            name=self.name, description=self.description, repository_data=repository_data
        )

        update_wrapper(repository_def, fn)
        return repository_def


@overload
def repository(name: Callable[..., Any]) -> RepositoryDefinition:
    ...


@overload
def repository(name: Optional[str] = ..., description: Optional[str] = ...) -> _Repository:
    ...


def repository(
    name: Optional[Union[str, Callable[..., Any]]] = None, description: Optional[str] = None
) -> Union[RepositoryDefinition, _Repository]:
    """Create a repository from the decorated function.

    The decorated function should take no arguments and its return value should one of:

    1. ``List[Union[JobDefinition, PipelineDefinition, PartitionSetDefinition, ScheduleDefinition, SensorDefinition]]``.
    Use this form when you have no need to lazy load pipelines or other definitions. This is the
    typical use case.

    2. A dict of the form:

    .. code-block:: python

        {
            'jobs': Dict[str, Callable[[], JobDefinition]],
            'pipelines': Dict[str, Callable[[], PipelineDefinition]],
            'partition_sets': Dict[str, Callable[[], PartitionSetDefinition]],
            'schedules': Dict[str, Callable[[], ScheduleDefinition]]
            'sensors': Dict[str, Callable[[], SensorDefinition]]
        }

    This form is intended to allow definitions to be created lazily when accessed by name,
    which can be helpful for performance when there are many definitions in a repository, or
    when constructing the definitions is costly.

    3. A :py:class:`RepositoryData`. Return this object if you need fine-grained
    control over the construction and indexing of definitions within the repository, e.g., to
    create definitions dynamically from .yaml files in a directory.

    Args:
        name (Optional[str]): The name of the repository. Defaults to the name of the decorated
            function.
        description (Optional[str]): A string description of the repository.

    Example:

    .. code-block:: python

        ######################################################################
        # A simple repository using the first form of the decorated function
        ######################################################################

        @op(config_schema={n: Field(Int)})
        def return_n(context):
            return context.op_config['n']

        @job
        def simple_job():
            return_n()

        @job
        def some_job():
            ...

        @sensor(job=some_job)
        def some_sensor():
            if foo():
                yield RunRequest(
                    run_key= ...,
                    run_config={
                        'ops': {'return_n': {'config': {'n': bar()}}}
                    }
                )

        @job
        def my_job():
            ...

        my_schedule = ScheduleDefinition(cron_schedule="0 0 * * *", job=my_job)

        @repository
        def simple_repository():
            return [simple_job, some_sensor, my_schedule]


        ######################################################################
        # A lazy-loaded repository
        ######################################################################

        def make_expensive_job():
            @job
            def expensive_job():
                for i in range(10000):
                    return_n.alias(f'return_n_{i}')()

            return expensive_job

        def make_expensive_schedule():
            @job
            def other_expensive_job():
                for i in range(11000):
                    return_n.alias(f'my_return_n_{i}')()

            return ScheduleDefinition(cron_schedule="0 0 * * *", job=other_expensive_job)

        @repository
        def lazy_loaded_repository():
            return {
                'jobs': {'expensive_job': make_expensive_job},
                'schedules': {'expensive_schedule': make_expensive_schedule}
            }


        ######################################################################
        # A complex repository that lazily constructs jobs from a directory
        # of files in a bespoke YAML format
        ######################################################################

        class ComplexRepositoryData(RepositoryData):
            def __init__(self, yaml_directory):
                self._yaml_directory = yaml_directory

            def get_all_pipelines(self):
                return [
                    self._construct_job_def_from_yaml_file(
                      self._yaml_file_for_job_name(file_name)
                    )
                    for file_name in os.listdir(self._yaml_directory)
                ]

            ...

        @repository
        def complex_repository():
            return ComplexRepositoryData('some_directory')

    """
    if callable(name):
        check.invariant(description is None)

        return _Repository()(name)

    return _Repository(name=name, description=description)
