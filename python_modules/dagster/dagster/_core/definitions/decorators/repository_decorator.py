from collections.abc import Iterable, Iterator, Mapping, Sequence
from functools import update_wrapper
from typing import TYPE_CHECKING, Callable, Optional, TypeVar, Union, overload

import dagster._check as check
from dagster._core.decorator_utils import get_function_params
from dagster._core.definitions.executor_definition import ExecutorDefinition
from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.logger_definition import LoggerDefinition
from dagster._core.definitions.metadata import RawMetadataValue, normalize_metadata
from dagster._core.definitions.partitions.partitioned_schedule import (
    UnresolvedPartitionedAssetScheduleDefinition,
)
from dagster._core.definitions.repository_definition import (
    VALID_REPOSITORY_DATA_DICT_KEYS,
    CachingRepositoryData,
    RepositoryData,
    RepositoryDefinition,
    RepositoryListSpec,
)
from dagster._core.definitions.repository_definition.repository_definition import RepositoryLoadData
from dagster._core.definitions.repository_definition.valid_definitions import RepositoryDictSpec
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.schedule_definition import ScheduleDefinition
from dagster._core.definitions.sensor_definition import SensorDefinition
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition
from dagster._core.errors import DagsterInvalidDefinitionError

if TYPE_CHECKING:
    from dagster._core.definitions.assets.definition.cacheable_assets_definition import (
        AssetsDefinitionCacheableData,
        CacheableAssetsDefinition,
    )
    from dagster._core.definitions.definitions_load_context import DefinitionsLoadContext
    from dagster.components.core.component_tree import ComponentTree

T = TypeVar("T")


def _flatten(items: Iterable[Union[T, list[T]]]) -> Iterator[T]:
    for x in items:
        if isinstance(x, list):
            # switch to `yield from _flatten(x)` to support multiple layers of nesting
            yield from x
        else:
            yield x


class _Repository:
    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Mapping[str, RawMetadataValue]] = None,
        default_executor_def: Optional[ExecutorDefinition] = None,
        default_logger_defs: Optional[Mapping[str, LoggerDefinition]] = None,
        top_level_resources: Optional[Mapping[str, ResourceDefinition]] = None,
        resource_key_mapping: Optional[Mapping[int, str]] = None,
        component_tree: Optional["ComponentTree"] = None,
    ):
        self.name = check.opt_str_param(name, "name")
        self.description = check.opt_str_param(description, "description")
        self.metadata = normalize_metadata(
            check.opt_mapping_param(metadata, "metadata", key_type=str)
        )
        self.default_executor_def = check.opt_inst_param(
            default_executor_def, "default_executor_def", ExecutorDefinition
        )
        self.default_logger_defs = check.opt_mapping_param(
            default_logger_defs, "default_logger_defs", key_type=str, value_type=LoggerDefinition
        )
        self.top_level_resources = check.opt_mapping_param(
            top_level_resources, "top_level_resources", key_type=str, value_type=ResourceDefinition
        )
        self.resource_key_mapping = check.opt_mapping_param(
            resource_key_mapping, "resource_key_mapping", key_type=int, value_type=str
        )
        self.component_tree = component_tree

    def __call__(
        self,
        fn: Union[
            Callable[[], RepositoryListSpec],
            Callable[[], RepositoryDictSpec],
        ],
    ) -> RepositoryDefinition:
        from dagster._core.definitions import AssetsDefinition, SourceAsset
        from dagster._core.definitions.assets.definition.cacheable_assets_definition import (
            CacheableAssetsDefinition,
        )
        from dagster._core.definitions.definitions_load_context import (
            DefinitionsLoadContext,
            DefinitionsLoadType,
        )

        check.callable_param(fn, "fn")

        if not self.name:
            self.name = fn.__name__

        cacheable_asset_data: dict[str, Sequence[AssetsDefinitionCacheableData]] = {}

        repository_definitions = fn()
        context = DefinitionsLoadContext.get()
        defs_state_info = context.defs_state_info

        if context.load_type == DefinitionsLoadType.INITIALIZATION:
            reconstruction_metadata = context.get_pending_reconstruction_metadata()
        else:
            reconstruction_metadata = context.reconstruction_metadata

        if isinstance(repository_definitions, list):
            bad_defns = []
            repository_defns = []
            for i, definition in enumerate(_flatten(repository_definitions)):
                if isinstance(definition, CacheableAssetsDefinition):
                    cacheable_data = _resolve_cacheable_asset_data(definition, context)
                    cacheable_asset_data[definition.unique_id] = cacheable_data
                    assets_defs = definition.build_definitions(cacheable_data)
                    repository_defns.extend(assets_defs)

                elif not isinstance(
                    definition,
                    (
                        JobDefinition,
                        ScheduleDefinition,
                        UnresolvedPartitionedAssetScheduleDefinition,
                        SensorDefinition,
                        GraphDefinition,
                        AssetsDefinition,
                        SourceAsset,
                        UnresolvedAssetJobDefinition,
                    ),
                ):
                    bad_defns.append((i, type(definition)))
                else:
                    repository_defns.append(definition)

            if bad_defns:
                bad_definitions_str = ", ".join(
                    [f"value of type {type_} at index {i}" for i, type_ in bad_defns]
                )
                raise DagsterInvalidDefinitionError(
                    "Bad return value from repository construction function: all elements of list "
                    "must be of type JobDefinition, GraphDefinition, "
                    "ScheduleDefinition, SensorDefinition, "
                    "AssetsDefinition, SourceAsset, or AssetChecksDefinition."
                    f"Got {bad_definitions_str}."
                )

            repository_data = CachingRepositoryData.from_list(
                repository_defns,
                default_executor_def=self.default_executor_def,
                default_logger_defs=self.default_logger_defs,
                top_level_resources=self.top_level_resources,
                component_tree=self.component_tree,
            )
            repository_load_data = (
                RepositoryLoadData(
                    cacheable_asset_data=cacheable_asset_data,
                    reconstruction_metadata=reconstruction_metadata,
                    defs_state_info=defs_state_info,
                )
                if cacheable_asset_data or reconstruction_metadata or defs_state_info
                else None
            )

        elif isinstance(repository_definitions, dict):
            if not set(repository_definitions.keys()).issubset(VALID_REPOSITORY_DATA_DICT_KEYS):
                raise DagsterInvalidDefinitionError(
                    "Bad return value from repository construction function: dict must not contain "
                    "keys other than {{'schedules', 'sensors', 'jobs'}}: found "
                    "{bad_keys}".format(
                        bad_keys=", ".join(
                            [
                                f"'{key}'"
                                for key in repository_definitions.keys()
                                if key not in VALID_REPOSITORY_DATA_DICT_KEYS
                            ]
                        )
                    )
                )
            repository_data = CachingRepositoryData.from_dict(repository_definitions)
            repository_load_data = None
        elif isinstance(repository_definitions, RepositoryData):
            repository_data = repository_definitions
            repository_load_data = None
        else:
            raise DagsterInvalidDefinitionError(
                f"Bad return value of type {type(repository_definitions)} from repository construction function: must "
                "return list, dict, or RepositoryData. See the @repository decorator docstring for "
                "details and examples",
            )

        repository_def = RepositoryDefinition(
            name=self.name,
            description=self.description,
            metadata=self.metadata,
            repository_data=repository_data,
            repository_load_data=repository_load_data,
        )

        update_wrapper(repository_def, fn)
        return repository_def


def _resolve_cacheable_asset_data(
    definition: "CacheableAssetsDefinition", context: "DefinitionsLoadContext"
) -> Sequence["AssetsDefinitionCacheableData"]:
    from dagster._core.definitions.definitions_load_context import DefinitionsLoadType

    if (
        context.load_type == DefinitionsLoadType.RECONSTRUCTION
        and definition.unique_id in context.cacheable_asset_data
    ):
        return context.cacheable_asset_data[definition.unique_id]
    # Error if some cacheable data is defined but the key is not found. If any
    # cacheable data is available, we expect all of it to be available. This
    # is to match previous behavior of PendingRepositoryDefinition.
    elif context.load_type == DefinitionsLoadType.RECONSTRUCTION and context.cacheable_asset_data:
        check.failed(
            f"No metadata found for CacheableAssetsDefinition with unique_id {definition.unique_id}."
        )
    else:
        return definition.compute_cacheable_data()


@overload
def repository(
    definitions_fn: Union[Callable[[], RepositoryListSpec], Callable[[], RepositoryDictSpec]],
) -> RepositoryDefinition: ...


@overload
def repository(
    *,
    name: Optional[str] = ...,
    description: Optional[str] = ...,
    metadata: Optional[Mapping[str, RawMetadataValue]] = ...,
    default_executor_def: Optional[ExecutorDefinition] = ...,
    default_logger_defs: Optional[Mapping[str, LoggerDefinition]] = ...,
    _top_level_resources: Optional[Mapping[str, ResourceDefinition]] = ...,
    _component_tree: Optional["ComponentTree"] = ...,
) -> _Repository: ...


def repository(
    definitions_fn: Optional[
        Union[
            Callable[[], RepositoryListSpec],
            Callable[[], RepositoryDictSpec],
        ]
    ] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    metadata: Optional[Mapping[str, RawMetadataValue]] = None,
    default_executor_def: Optional[ExecutorDefinition] = None,
    default_logger_defs: Optional[Mapping[str, LoggerDefinition]] = None,
    _top_level_resources: Optional[Mapping[str, ResourceDefinition]] = None,
    _component_tree: Optional["ComponentTree"] = None,
) -> Union[RepositoryDefinition, _Repository]:
    """Create a repository from the decorated function.

    In most cases, :py:class:`Definitions` should be used instead.

    The decorated function should take no arguments and its return value should one of:

    1. ``List[Union[JobDefinition, ScheduleDefinition, SensorDefinition]]``.
    Use this form when you have no need to lazy load jobs or other definitions. This is the
    typical use case.

    2. A dict of the form:

    .. code-block:: python

        {
            'jobs': Dict[str, Callable[[], JobDefinition]],
            'schedules': Dict[str, Callable[[], ScheduleDefinition]],
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
        metadata (Optional[Dict[str, RawMetadataValue]]): Arbitrary metadata for the repository. Not
            displayed in the UI but accessible on RepositoryDefinition at runtime.
        top_level_resources (Optional[Mapping[str, ResourceDefinition]]): A dict of top-level
            resource keys to defintions, for resources which should be displayed in the UI.

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
                        run_key=...,
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
            # A simple repository using the first form of the decorated function
            # and custom metadata that will be displayed in the UI
            ######################################################################

            ...

            @repository(
                name='my_repo',
                metadata={
                    'team': 'Team A',
                    'repository_version': '1.2.3',
                    'environment': 'production',
                })
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

                def get_all_jobs(self):
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
    if definitions_fn is not None:
        check.invariant(description is None)
        check.invariant(len(get_function_params(definitions_fn)) == 0)

        return _Repository()(definitions_fn)

    return _Repository(
        name=name,
        description=description,
        metadata=metadata,
        default_executor_def=default_executor_def,
        default_logger_defs=default_logger_defs,
        top_level_resources=_top_level_resources,
        component_tree=_component_tree,
    )
