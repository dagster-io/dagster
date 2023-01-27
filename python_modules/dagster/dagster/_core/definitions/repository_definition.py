from abc import ABC, abstractmethod
from inspect import isfunction
from types import FunctionType
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Type,
    TypeVar,
    Union,
    cast,
)

import dagster._check as check
from dagster._annotations import public
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster._core.instance import DagsterInstance
from dagster._core.selector import parse_solid_selection
from dagster._serdes import whitelist_for_serdes
from dagster._utils import make_readonly_value
from dagster._utils.merger import merge_dicts

from .asset_selection import AssetGraph
from .assets_job import ASSET_BASE_JOB_PREFIX, get_base_asset_jobs, is_base_asset_job_name
from .cacheable_assets import AssetsDefinitionCacheableData
from .events import AssetKey, CoercibleToAssetKey
from .executor_definition import ExecutorDefinition
from .graph_definition import GraphDefinition, SubselectedGraphDefinition
from .job_definition import JobDefinition
from .logger_definition import LoggerDefinition
from .partition import PartitionScheduleDefinition, PartitionSetDefinition
from .pipeline_definition import PipelineDefinition
from .schedule_definition import ScheduleDefinition
from .sensor_definition import SensorDefinition
from .source_asset import SourceAsset
from .unresolved_asset_job_definition import UnresolvedAssetJobDefinition
from .utils import check_valid_name

if TYPE_CHECKING:
    from dagster._core.definitions import AssetGroup, AssetsDefinition
    from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition
    from dagster._core.storage.asset_value_loader import AssetValueLoader


SINGLETON_REPOSITORY_NAME = "__repository__"

VALID_REPOSITORY_DATA_DICT_KEYS = {
    "pipelines",
    "partition_sets",
    "schedules",
    "sensors",
    "jobs",
}

RepositoryLevelDefinition = TypeVar(
    "RepositoryLevelDefinition",
    PipelineDefinition,
    JobDefinition,
    PartitionSetDefinition,
    ScheduleDefinition,
    SensorDefinition,
)

RepositoryListDefinition = Union[
    "AssetsDefinition",
    "AssetGroup",
    GraphDefinition,
    PartitionSetDefinition[object],
    PipelineDefinition,
    ScheduleDefinition,
    SensorDefinition,
    SourceAsset,
    UnresolvedAssetJobDefinition,
]


@whitelist_for_serdes
class RepositoryLoadData(
    NamedTuple(
        "_RepositoryLoadData",
        [
            ("cached_data_by_key", Mapping[str, Sequence[AssetsDefinitionCacheableData]]),
        ],
    )
):
    def __new__(cls, cached_data_by_key: Mapping[str, Sequence[AssetsDefinitionCacheableData]]):
        return super(RepositoryLoadData, cls).__new__(
            cls,
            cached_data_by_key=make_readonly_value(
                check.mapping_param(
                    cached_data_by_key,
                    "cached_data_by_key",
                    key_type=str,
                    value_type=list,
                )
            ),
        )


class _CacheingDefinitionIndex(Generic[RepositoryLevelDefinition]):
    def __init__(
        self,
        definition_class: Type[RepositoryLevelDefinition],
        definition_class_name: str,
        definition_kind: str,
        definitions: Mapping[
            str, Union[RepositoryLevelDefinition, Callable[[], RepositoryLevelDefinition]]
        ],
        validation_fn: Callable[[RepositoryLevelDefinition], RepositoryLevelDefinition],
        lazy_definitions_fn: Optional[Callable[[], Sequence[RepositoryLevelDefinition]]] = None,
    ):
        """
        Args:
            definitions: A dictionary of definition names to definitions or functions that load
                definitions.
            lazy_definitions_fn: A function for loading a list of definitions whose names are not
                even known until loaded.

        """
        for key, definition in definitions.items():
            check.invariant(
                isinstance(definition, definition_class) or callable(definition),
                "Bad definition for {definition_kind} {key}: must be {definition_class_name} or "
                "callable, got {type_}".format(
                    definition_kind=definition_kind,
                    key=key,
                    definition_class_name=definition_class_name,
                    type_=type(definition),
                ),
            )

        self._definition_class: Type[RepositoryLevelDefinition] = definition_class
        self._definition_class_name = definition_class_name
        self._definition_kind = definition_kind
        self._validation_fn: Callable[
            [RepositoryLevelDefinition], RepositoryLevelDefinition
        ] = validation_fn

        self._definitions: Mapping[
            str, Union[RepositoryLevelDefinition, Callable[[], RepositoryLevelDefinition]]
        ] = definitions
        self._definition_cache: Dict[str, RepositoryLevelDefinition] = {}
        self._definition_names: Optional[Sequence[str]] = None

        self._lazy_definitions_fn: Callable[
            [], Sequence[RepositoryLevelDefinition]
        ] = lazy_definitions_fn or (lambda: [])
        self._lazy_definitions: Optional[Sequence[RepositoryLevelDefinition]] = None

        self._all_definitions: Optional[Sequence[RepositoryLevelDefinition]] = None

    def _get_lazy_definitions(self) -> Sequence[RepositoryLevelDefinition]:
        if self._lazy_definitions is None:
            self._lazy_definitions = self._lazy_definitions_fn()
            for definition in self._lazy_definitions:
                self._validate_and_cache_definition(definition, definition.name)

        return self._lazy_definitions

    def get_definition_names(self) -> Sequence[str]:
        if self._definition_names:
            return self._definition_names

        lazy_names = []
        for definition in self._get_lazy_definitions():
            strict_definition = self._definitions.get(definition.name)
            if strict_definition:
                check.invariant(
                    strict_definition == definition,
                    f"Duplicate definition found for {definition.name}",
                )
            else:
                lazy_names.append(definition.name)

        self._definition_names = list(self._definitions.keys()) + lazy_names
        return self._definition_names

    def has_definition(self, definition_name: str) -> bool:
        check.str_param(definition_name, "definition_name")

        return definition_name in self.get_definition_names()

    def get_all_definitions(self) -> Sequence[RepositoryLevelDefinition]:
        if self._all_definitions is not None:
            return self._all_definitions

        self._all_definitions = list(
            sorted(
                map(self.get_definition, self.get_definition_names()),
                key=lambda definition: definition.name,
            )
        )
        return self._all_definitions

    def get_definition(self, definition_name: str) -> RepositoryLevelDefinition:
        check.str_param(definition_name, "definition_name")

        if not self.has_definition(definition_name):
            raise DagsterInvariantViolationError(
                "Could not find {definition_kind} '{definition_name}'. Found: "
                "{found_names}.".format(
                    definition_kind=self._definition_kind,
                    definition_name=definition_name,
                    found_names=", ".join(
                        [
                            "'{found_name}'".format(found_name=found_name)
                            for found_name in self.get_definition_names()
                        ]
                    ),
                )
            )

        if definition_name in self._definition_cache:
            return self._definition_cache[definition_name]

        definition_source = self._definitions[definition_name]

        if isinstance(definition_source, self._definition_class):
            self._definition_cache[definition_name] = self._validation_fn(definition_source)
            return definition_source
        else:
            definition = cast(Callable, definition_source)()
            self._validate_and_cache_definition(definition, definition_name)
            return definition

    def _validate_and_cache_definition(
        self, definition: RepositoryLevelDefinition, definition_dict_key: str
    ):
        check.invariant(
            isinstance(definition, self._definition_class),
            "Bad constructor for {definition_kind} {definition_name}: must return "
            "{definition_class_name}, got value of type {type_}".format(
                definition_kind=self._definition_kind,
                definition_name=definition_dict_key,
                definition_class_name=self._definition_class_name,
                type_=type(definition),
            ),
        )
        check.invariant(
            definition.name == definition_dict_key,
            "Bad constructor for {definition_kind} '{definition_name}': name in "
            "{definition_class_name} does not match: got '{definition_def_name}'".format(
                definition_kind=self._definition_kind,
                definition_name=definition_dict_key,
                definition_class_name=self._definition_class_name,
                definition_def_name=definition.name,
            ),
        )
        self._definition_cache[definition_dict_key] = self._validation_fn(definition)


class RepositoryData(ABC):
    """
    Users should usually rely on the :py:func:`@repository <repository>` decorator to create new
    repositories, which will in turn call the static constructors on this class. However, users may
    subclass :py:class:`RepositoryData` for fine-grained control over access to and lazy creation
    of repository members.
    """

    @abstractmethod
    def get_all_pipelines(self) -> Sequence[PipelineDefinition]:
        """Return all pipelines/jobs in the repository as a list.

        Returns:
            List[PipelineDefinition]: All pipelines/jobs in the repository.
        """

    @public
    def get_all_jobs(self) -> Sequence[JobDefinition]:
        """Return all jobs in the repository as a list.

        Returns:
            List[JobDefinition]: All jobs in the repository.
        """
        return [job for job in self.get_all_pipelines() if isinstance(job, JobDefinition)]

    def get_pipeline_names(self) -> Sequence[str]:
        """Get the names of all pipelines/jobs in the repository.

        Returns:
            List[str]
        """
        return [pipeline_def.name for pipeline_def in self.get_all_pipelines()]

    @public
    def get_job_names(self) -> Sequence[str]:
        """Get the names of all jobs in the repository.

        Returns:
            List[str]
        """
        return [job_def.name for job_def in self.get_all_jobs()]

    def has_pipeline(self, pipeline_name: str) -> bool:
        """Check if a pipeline/job with a given name is present in the repository.

        Args:
            pipeline_name (str): The name of the pipeline/job.

        Returns:
            bool
        """
        return pipeline_name in self.get_pipeline_names()

    @public
    def has_job(self, job_name: str) -> bool:
        """Check if a job with a given name is present in the repository.

        Args:
            job_name (str): The name of the job.

        Returns:
            bool
        """
        return job_name in self.get_job_names()

    def get_pipeline(self, pipeline_name) -> PipelineDefinition:
        """Get a pipeline/job by name.

        Args:
            pipeline_name (str): Name of the pipeline/job to retrieve.

        Returns:
            PipelineDefinition: The pipeline/job definition corresponding to the given name.
        """
        pipelines_with_name = [
            pipeline for pipeline in self.get_all_pipelines() if pipeline.name == pipeline_name
        ]
        if not pipelines_with_name:
            raise DagsterInvariantViolationError(
                f"Could not find pipeline/job {pipeline_name} in repository"
            )
        return pipelines_with_name[0]

    @public
    def get_job(self, job_name: str) -> JobDefinition:
        """Get a job by name.

        Args:
            job_name (str): Name of the job to retrieve.

        Returns:
            JobDefinition: The job definition corresponding to the given name.
        """
        match = next(job for job in self.get_all_jobs() if job.name == job_name)
        if match is None:
            raise DagsterInvariantViolationError(f"Could not find job {job_name} in repository")
        return match

    def get_partition_set_names(self):
        """Get the names of all partition sets in the repository.

        Returns:
            List[str]
        """
        return [partition_set.name for partition_set in self.get_all_partition_sets()]

    def has_partition_set(self, partition_set_name: str) -> bool:
        """Check if a partition set with a given name is present in the repository.

        Args:
            partition_set_name (str): The name of the partition set.

        Returns:
            bool
        """
        return partition_set_name in self.get_partition_set_names()

    def get_all_partition_sets(self) -> Sequence[PartitionSetDefinition]:
        """Return all partition sets in the repository as a list.

        Returns:
            List[PartitionSetDefinition]: All partition sets in the repository.
        """
        return []

    def get_partition_set(self, partition_set_name: str) -> PartitionSetDefinition:
        """Get a partition set by name.

        Args:
            partition_set_name (str): Name of the partition set to retrieve.

        Returns:
            PartitionSetDefinition: The partition set definition corresponding to the given name.
        """
        partition_sets_with_name = [
            partition_set
            for partition_set in self.get_all_partition_sets()
            if partition_set.name == partition_set_name
        ]
        if not partition_sets_with_name:
            raise DagsterInvariantViolationError(
                f"Could not find partition set {partition_set_name} in repository"
            )
        return partition_sets_with_name[0]

    @public
    def get_schedule_names(self) -> Sequence[str]:
        """Get the names of all schedules in the repository.

        Returns:
            List[str]
        """
        return [schedule.name for schedule in self.get_all_schedules()]

    @public
    def get_all_schedules(self) -> Sequence[ScheduleDefinition]:
        """Return all schedules in the repository as a list.

        Returns:
            List[ScheduleDefinition]: All pipelines in the repository.
        """
        return []

    @public
    def get_schedule(self, schedule_name: str) -> ScheduleDefinition:
        """Get a schedule by name.

        args:
            schedule_name (str): name of the schedule to retrieve.

        Returns:
            ScheduleDefinition: The schedule definition corresponding to the given name.
        """
        schedules_with_name = [
            schedule for schedule in self.get_all_schedules() if schedule.name == schedule_name
        ]
        if not schedules_with_name:
            raise DagsterInvariantViolationError(
                f"Could not find schedule {schedule_name} in repository"
            )
        return schedules_with_name[0]

    def has_schedule(self, schedule_name: str) -> bool:
        return schedule_name in self.get_schedule_names()

    @public
    def get_all_sensors(self) -> Sequence[SensorDefinition]:
        return []

    @public
    def get_sensor_names(self) -> Sequence[str]:
        return [sensor.name for sensor in self.get_all_sensors()]

    @public
    def get_sensor(self, sensor_name: str) -> SensorDefinition:
        sensors_with_name = [
            sensor for sensor in self.get_all_sensors() if sensor.name == sensor_name
        ]
        if not sensors_with_name:
            raise DagsterInvariantViolationError(
                f"Could not find sensor {sensor_name} in repository"
            )
        return sensors_with_name[0]

    @public
    def has_sensor(self, sensor_name: str) -> bool:
        return sensor_name in self.get_sensor_names()

    @public
    def get_source_assets_by_key(self) -> Mapping[AssetKey, SourceAsset]:
        return {}

    def load_all_definitions(self):
        # force load of all lazy constructed code artifacts
        self.get_all_pipelines()
        self.get_all_jobs()
        self.get_all_partition_sets()
        self.get_all_schedules()
        self.get_all_sensors()
        self.get_source_assets_by_key()


T = TypeVar("T")
Resolvable = Callable[[], T]


class CachingRepositoryData(RepositoryData):
    """Default implementation of RepositoryData used by the :py:func:`@repository <repository>` decorator.
    """

    _all_jobs: Optional[Sequence[JobDefinition]]
    _all_pipelines: Optional[Sequence[PipelineDefinition]]

    def __init__(
        self,
        pipelines: Mapping[str, Union[PipelineDefinition, Resolvable[PipelineDefinition]]],
        jobs: Mapping[str, Union[JobDefinition, Resolvable[JobDefinition]]],
        partition_sets: Mapping[
            str, Union[PartitionSetDefinition, Resolvable[PartitionSetDefinition]]
        ],
        schedules: Mapping[str, Union[ScheduleDefinition, Resolvable[ScheduleDefinition]]],
        sensors: Mapping[str, Union[SensorDefinition, Resolvable[SensorDefinition]]],
        source_assets_by_key: Mapping[AssetKey, SourceAsset],
        assets_defs_by_key: Mapping[AssetKey, "AssetsDefinition"],
    ):
        """Constructs a new CachingRepositoryData object.

        You may pass pipeline, job, partition_set, and schedule definitions directly, or you may pass
        callables with no arguments that will be invoked to lazily construct definitions when
        accessed by name. This can be helpful for performance when there are many definitions in a
        repository, or when constructing the definitions is costly.

        Note that when lazily constructing a definition, the name of the definition must match its
        key in its dictionary index, or a :py:class:`DagsterInvariantViolationError` will be thrown
        at retrieval time.

        Args:
            pipelines (Mapping[str, Union[PipelineDefinition, Callable[[], PipelineDefinition]]]):
                The pipeline definitions belonging to the repository.
            jobs (Mapping[str, Union[JobDefinition, Callable[[], JobDefinition]]]):
                The job definitions belonging to the repository.
            partition_sets (Mapping[str, Union[PartitionSetDefinition, Callable[[], PartitionSetDefinition]]]):
                The partition sets belonging to the repository.
            schedules (Mapping[str, Union[ScheduleDefinition, Callable[[], ScheduleDefinition]]]):
                The schedules belonging to the repository.
            sensors (Mapping[str, Union[SensorDefinition, Callable[[], SensorDefinition]]]):
                The sensors belonging to a repository.
            source_assets_by_key (Mapping[AssetKey, SourceAsset]): The source assets belonging to a repository.
            assets_defs_by_key (Mapping[AssetKey, AssetsDefinition]): The assets definitions
                belonging to a repository.
        """
        from dagster._core.definitions import AssetsDefinition

        check.mapping_param(
            pipelines, "pipelines", key_type=str, value_type=(PipelineDefinition, FunctionType)
        )
        check.mapping_param(jobs, "jobs", key_type=str, value_type=(JobDefinition, FunctionType))
        check.mapping_param(
            partition_sets,
            "partition_sets",
            key_type=str,
            value_type=(PartitionSetDefinition, FunctionType),
        )
        check.mapping_param(
            schedules, "schedules", key_type=str, value_type=(ScheduleDefinition, FunctionType)
        )
        check.mapping_param(
            sensors, "sensors", key_type=str, value_type=(SensorDefinition, FunctionType)
        )
        check.mapping_param(
            source_assets_by_key, "source_assets_by_key", key_type=AssetKey, value_type=SourceAsset
        )
        check.mapping_param(
            assets_defs_by_key, "assets_defs_by_key", key_type=AssetKey, value_type=AssetsDefinition
        )

        self._pipelines = _CacheingDefinitionIndex(
            PipelineDefinition,
            "PipelineDefinition",
            "pipeline",
            pipelines,
            self._validate_pipeline,
        )

        self._jobs = _CacheingDefinitionIndex(
            JobDefinition,
            "JobDefinition",
            "job",
            jobs,
            self._validate_job,
        )

        self._schedules = _CacheingDefinitionIndex(
            ScheduleDefinition,
            "ScheduleDefinition",
            "schedule",
            schedules,
            self._validate_schedule,
        )
        schedule_partition_sets = filter(
            None,
            [
                _get_partition_set_from_schedule(schedule)
                for schedule in self._schedules.get_all_definitions()
            ],
        )
        self._source_assets_by_key = source_assets_by_key
        self._assets_defs_by_key = assets_defs_by_key

        def load_partition_sets_from_pipelines() -> Sequence[PartitionSetDefinition]:
            job_partition_sets = []
            for pipeline in self.get_all_pipelines():
                if isinstance(pipeline, JobDefinition):
                    job_partition_set = pipeline.get_partition_set_def()

                    if job_partition_set:
                        # should only return a partition set if this was constructed using the job
                        # API, with a partitioned config
                        job_partition_sets.append(job_partition_set)

            return job_partition_sets

        self._partition_sets = _CacheingDefinitionIndex(
            PartitionSetDefinition,
            "PartitionSetDefinition",
            "partition set",
            merge_dicts(
                {partition_set.name: partition_set for partition_set in schedule_partition_sets},
                partition_sets,
            ),
            self._validate_partition_set,
            load_partition_sets_from_pipelines,
        )
        self._sensors = _CacheingDefinitionIndex(
            SensorDefinition,
            "SensorDefinition",
            "sensor",
            sensors,
            self._validate_sensor,
        )
        # load all sensors to force validation
        self._sensors.get_all_definitions()

        self._all_pipelines = None
        self._all_jobs = None

    @staticmethod
    def from_dict(repository_definitions: Dict[str, Dict[str, Any]]) -> "CachingRepositoryData":
        """Static constructor.

        Args:
            repository_definition (Dict[str, Dict[str, ...]]): A dict of the form:

                {
                    'pipelines': Dict[str, Callable[[], PipelineDefinition]],
                    'jobs': Dict[str, Callable[[], JobDefinition]],
                    'partition_sets': Dict[str, Callable[[], PartitionSetDefinition]],
                    'schedules': Dict[str, Callable[[], ScheduleDefinition]]
                }

            This form is intended to allow definitions to be created lazily when accessed by name,
            which can be helpful for performance when there are many definitions in a repository, or
            when constructing the definitions is costly.
        """
        check.dict_param(repository_definitions, "repository_definitions", key_type=str)
        check.invariant(
            set(repository_definitions.keys()).issubset(VALID_REPOSITORY_DATA_DICT_KEYS),
            "Bad dict: must not contain keys other than {{{valid_keys}}}: found {bad_keys}.".format(
                valid_keys=", ".join(
                    ["'{key}'".format(key=key) for key in VALID_REPOSITORY_DATA_DICT_KEYS]
                ),
                bad_keys=", ".join(
                    [
                        "'{key}'"
                        for key in repository_definitions.keys()
                        if key not in VALID_REPOSITORY_DATA_DICT_KEYS
                    ]
                ),
            ),
        )

        for key in VALID_REPOSITORY_DATA_DICT_KEYS:
            if key not in repository_definitions:
                repository_definitions[key] = {}

        duplicate_keys = set(repository_definitions["schedules"].keys()).intersection(
            set(repository_definitions["sensors"].keys())
        )
        if duplicate_keys:
            raise DagsterInvalidDefinitionError(
                "Duplicate definitions between schedules and sensors found for keys:"
                f" {', '.join(duplicate_keys)}"
            )

        # merge jobs in to pipelines while they are just implemented as pipelines
        for key, job in repository_definitions["jobs"].items():
            if key in repository_definitions["pipelines"]:
                raise DagsterInvalidDefinitionError(
                    f'Conflicting entries for name {key} in "jobs" and "pipelines".'
                )

            if isinstance(job, GraphDefinition):
                repository_definitions["jobs"][key] = job.coerce_to_job()
            elif isinstance(job, UnresolvedAssetJobDefinition):
                repository_definitions["jobs"][key] = job.resolve(
                    # TODO: https://github.com/dagster-io/dagster/issues/8263
                    assets=[],
                    source_assets=[],
                    default_executor_def=None,
                )
            elif not isinstance(job, JobDefinition) and not isfunction(job):
                raise DagsterInvalidDefinitionError(
                    f"Object mapped to {key} is not an instance of JobDefinition or"
                    " GraphDefinition."
                )

        return CachingRepositoryData(
            **repository_definitions, source_assets_by_key={}, assets_defs_by_key={}
        )

    @classmethod
    def from_list(
        cls,
        repository_definitions: Sequence[RepositoryListDefinition],
        default_executor_def: Optional[ExecutorDefinition] = None,
        default_logger_defs: Optional[Mapping[str, LoggerDefinition]] = None,
    ) -> "CachingRepositoryData":
        """Static constructor.

        Args:
            repository_definitions (List[Union[PipelineDefinition, PartitionSetDefinition, ScheduleDefinition, SensorDefinition, AssetGroup, GraphDefinition]]):
                Use this constructor when you have no need to lazy load pipelines/jobs or other
                definitions.
        """
        from dagster._core.definitions import AssetGroup, AssetsDefinition

        pipelines_or_jobs: Dict[str, Union[PipelineDefinition, JobDefinition]] = {}
        coerced_graphs: Dict[str, JobDefinition] = {}
        unresolved_jobs: Dict[str, UnresolvedAssetJobDefinition] = {}
        partition_sets: Dict[str, PartitionSetDefinition[object]] = {}
        schedules: Dict[str, ScheduleDefinition] = {}
        sensors: Dict[str, SensorDefinition] = {}
        assets_defs: List[AssetsDefinition] = []
        asset_keys: Set[AssetKey] = set()
        source_assets: List[SourceAsset] = []
        combined_asset_group = None
        for definition in repository_definitions:
            if isinstance(definition, PipelineDefinition):
                if (
                    definition.name in pipelines_or_jobs
                    and pipelines_or_jobs[definition.name] != definition
                ) or definition.name in unresolved_jobs:
                    raise DagsterInvalidDefinitionError(
                        f"Duplicate {definition.target_type} definition found for"
                        f" {definition.describe_target()}"
                    )
                if is_base_asset_job_name(definition.name):
                    raise DagsterInvalidDefinitionError(
                        f"Attempted to provide job called {definition.name} to repository, which "
                        "is a reserved name. Please rename the job."
                    )
                pipelines_or_jobs[definition.name] = definition
            elif isinstance(definition, PartitionSetDefinition):
                if definition.name in partition_sets:
                    raise DagsterInvalidDefinitionError(
                        "Duplicate partition set definition found for partition set"
                        f" {definition.name}"
                    )
                partition_sets[definition.name] = definition
            elif isinstance(definition, SensorDefinition):
                if definition.name in sensors or definition.name in schedules:
                    raise DagsterInvalidDefinitionError(
                        f"Duplicate definition found for {definition.name}"
                    )
                sensors[definition.name] = definition
            elif isinstance(definition, ScheduleDefinition):
                if definition.name in sensors or definition.name in schedules:
                    raise DagsterInvalidDefinitionError(
                        f"Duplicate definition found for {definition.name}"
                    )
                schedules[definition.name] = definition
                partition_set_def = _get_partition_set_from_schedule(definition)
                if partition_set_def:
                    if (
                        partition_set_def.name in partition_sets
                        and partition_set_def != partition_sets[partition_set_def.name]
                    ):
                        raise DagsterInvalidDefinitionError(
                            "Duplicate partition set definition found for partition set "
                            f"{partition_set_def.name}"
                        )
                    partition_sets[partition_set_def.name] = partition_set_def
            elif isinstance(definition, GraphDefinition):
                coerced = definition.coerce_to_job()
                if coerced.name in pipelines_or_jobs:
                    raise DagsterInvalidDefinitionError(
                        f"Duplicate {coerced.target_type} definition found for graph"
                        f" '{coerced.name}'"
                    )
                pipelines_or_jobs[coerced.name] = coerced
                coerced_graphs[coerced.name] = coerced
            elif isinstance(definition, UnresolvedAssetJobDefinition):
                if definition.name in pipelines_or_jobs or definition.name in unresolved_jobs:
                    raise DagsterInvalidDefinitionError(
                        f"Duplicate definition found for unresolved job '{definition.name}'"
                    )
                # we can only resolve these once we have all assets
                unresolved_jobs[definition.name] = definition
            elif isinstance(definition, AssetGroup):
                if combined_asset_group:
                    combined_asset_group += definition
                else:
                    combined_asset_group = definition
            elif isinstance(definition, AssetsDefinition):
                for key in definition.keys:
                    if key in asset_keys:
                        raise DagsterInvalidDefinitionError(f"Duplicate asset key: {key}")

                asset_keys.update(definition.keys)
                assets_defs.append(definition)
            elif isinstance(definition, SourceAsset):
                source_assets.append(definition)
            else:
                check.failed(f"Unexpected repository entry {definition}")

        if assets_defs or source_assets:
            if combined_asset_group is not None:
                raise DagsterInvalidDefinitionError(
                    "A repository can't have both an AssetGroup and direct asset defs"
                )
            combined_asset_group = AssetGroup(
                assets=assets_defs,
                source_assets=source_assets,
                executor_def=default_executor_def,
            )

        if combined_asset_group:
            for job_def in get_base_asset_jobs(
                assets=combined_asset_group.assets,
                source_assets=combined_asset_group.source_assets,
                executor_def=combined_asset_group.executor_def,
                resource_defs=combined_asset_group.resource_defs,
            ):
                pipelines_or_jobs[job_def.name] = job_def

            source_assets_by_key = {
                source_asset.key: source_asset
                for source_asset in combined_asset_group.source_assets
            }
            assets_defs_by_key = {
                key: asset for asset in combined_asset_group.assets for key in asset.keys
            }
        else:
            source_assets_by_key = {}
            assets_defs_by_key = {}

        for name, sensor_def in sensors.items():
            if sensor_def.has_loadable_targets():
                targets = sensor_def.load_targets()
                for target in targets:
                    _process_and_validate_target(
                        sensor_def, coerced_graphs, unresolved_jobs, pipelines_or_jobs, target
                    )

        for name, schedule_def in schedules.items():
            if schedule_def.has_loadable_target():
                target = schedule_def.load_target()
                _process_and_validate_target(
                    schedule_def, coerced_graphs, unresolved_jobs, pipelines_or_jobs, target
                )

        # resolve all the UnresolvedAssetJobDefinitions using the full set of assets
        for name, unresolved_job_def in unresolved_jobs.items():
            if not combined_asset_group:
                raise DagsterInvalidDefinitionError(
                    f"UnresolvedAssetJobDefinition {name} specified, but no AssetsDefinitions exist"
                    " on the repository."
                )
            resolved_job = unresolved_job_def.resolve(
                assets=combined_asset_group.assets,
                source_assets=combined_asset_group.source_assets,
                default_executor_def=default_executor_def,
            )
            pipelines_or_jobs[name] = resolved_job

        pipelines: Dict[str, PipelineDefinition] = {}
        jobs: Dict[str, JobDefinition] = {}
        for name, pipeline_or_job in pipelines_or_jobs.items():
            if isinstance(pipeline_or_job, JobDefinition):
                jobs[name] = pipeline_or_job
            else:
                pipelines[name] = pipeline_or_job

        if default_executor_def:
            for name, job_def in jobs.items():
                if not job_def._executor_def_specified:  # pylint: disable=protected-access
                    jobs[name] = job_def.with_executor_def(default_executor_def)

        if default_logger_defs:
            for name, job_def in jobs.items():
                if not job_def._logger_defs_specified:  # pylint: disable=protected-access
                    jobs[name] = job_def.with_logger_defs(default_logger_defs)

        return CachingRepositoryData(
            pipelines=pipelines,
            jobs=jobs,
            partition_sets=partition_sets,
            schedules=schedules,
            sensors=sensors,
            source_assets_by_key=source_assets_by_key,
            assets_defs_by_key=assets_defs_by_key,
        )

    def get_pipeline_names(self) -> Sequence[str]:
        """Get the names of all pipelines/jobs in the repository.

        Returns:
            List[str]
        """
        return [*self._pipelines.get_definition_names(), *self.get_job_names()]

    def get_job_names(self) -> Sequence[str]:
        """Get the names of all jobs in the repository.

        Returns:
            List[str]
        """
        return self._jobs.get_definition_names()

    def has_pipeline(self, pipeline_name: str) -> bool:
        """Check if a pipeline/job with a given name is present in the repository.

        Args:
            pipeline_name (str): The name of the pipeline/job.

        Returns:
            bool
        """
        check.str_param(pipeline_name, "pipeline_name")

        return self._pipelines.has_definition(pipeline_name) or self._jobs.has_definition(
            pipeline_name
        )

    def has_job(self, job_name: str) -> bool:
        """Check if a job with a given name is present in the repository.

        Args:
            job_name (str): The name of the job.

        Returns:
            bool
        """
        check.str_param(job_name, "job_name")
        return self._jobs.has_definition(job_name)

    def get_all_pipelines(self) -> Sequence[PipelineDefinition]:
        """Return all pipelines/jobs in the repository as a list.

        Note that this will construct any pipeline/job that has not yet been constructed.

        Returns:
            List[PipelineDefinition]: All pipelines/jobs in the repository.
        """
        if self._all_pipelines is not None:
            return self._all_pipelines

        self._all_jobs = self._jobs.get_all_definitions()
        pipelines: List[PipelineDefinition] = [
            *self._pipelines.get_all_definitions(),
            *self._all_jobs,
        ]
        self._check_solid_defs(pipelines)
        self._all_pipelines = pipelines
        return self._all_pipelines

    def get_all_jobs(self) -> Sequence[JobDefinition]:
        """Return all jobs in the repository as a list.

        Note that this will construct any job that has not yet been constructed.

        Returns:
            List[JobDefinition]: All jobs in the repository.
        """
        if self._all_jobs is not None:
            return self._all_jobs

        # _check_solid_defs enforces that pipeline and graph definition names are
        # unique within a repository. Loads pipelines in the line below to enforce
        # pipeline/job/graph uniqueness.
        self.get_all_pipelines()

        # The `get_all_pipelines` call ensures _all_jobs is set.
        return cast(Sequence[JobDefinition], self._all_jobs)

    def get_pipeline(self, pipeline_name: str) -> PipelineDefinition:
        """Get a pipeline/job by name.

        If this pipeline/job has not yet been constructed, only this pipeline/job is constructed, and will
        be cached for future calls.

        Args:
            pipeline_name (str): Name of the pipeline/job to retrieve.

        Returns:
            PipelineDefinition: The pipeline/job definition corresponding to the given name.
        """
        check.str_param(pipeline_name, "pipeline_name")

        if self._jobs.has_definition(pipeline_name):
            return self._jobs.get_definition(pipeline_name)
        else:
            return self._pipelines.get_definition(pipeline_name)

    def get_job(self, job_name: str) -> JobDefinition:
        """Get a job by name.

        If this job has not yet been constructed, only this job is constructed, and will
        be cached for future calls.

        Args:
            job_name (str): Name of the job to retrieve.

        Returns:
            JobDefinition: The job definition corresponding to the given name.
        """
        check.str_param(job_name, "job_name")
        return self._jobs.get_definition(job_name)

    def get_partition_set_names(self) -> Sequence[str]:
        """Get the names of all partition sets in the repository.

        Returns:
            List[str]
        """
        return self._partition_sets.get_definition_names()

    def has_partition_set(self, partition_set_name: str) -> bool:
        """Check if a partition set with a given name is present in the repository.

        Args:
            partition_set_name (str): The name of the partition set.

        Returns:
            bool
        """
        check.str_param(partition_set_name, "partition_set_name")
        return self._partition_sets.has_definition(partition_set_name)

    def get_all_partition_sets(self) -> Sequence[PartitionSetDefinition]:
        """Return all partition sets in the repository as a list.

        Note that this will construct any partition set that has not yet been constructed.

        Returns:
            List[PartitionSetDefinition]: All partition sets in the repository.
        """
        return self._partition_sets.get_all_definitions()

    def get_partition_set(self, partition_set_name: str) -> PartitionSetDefinition:
        """Get a partition set by name.

        If this partition set has not yet been constructed, only this partition set is constructed,
        and will be cached for future calls.

        Args:
            partition_set_name (str): Name of the partition set to retrieve.

        Returns:
            PartitionSetDefinition: The partition set definition corresponding to the given name.
        """
        check.str_param(partition_set_name, "partition_set_name")

        return self._partition_sets.get_definition(partition_set_name)

    def get_schedule_names(self) -> Sequence[str]:
        """Get the names of all schedules in the repository.

        Returns:
            List[str]
        """
        return self._schedules.get_definition_names()

    def get_all_schedules(self) -> Sequence[ScheduleDefinition]:
        """Return all schedules in the repository as a list.

        Note that this will construct any schedule that has not yet been constructed.

        Returns:
            List[ScheduleDefinition]: All schedules in the repository.
        """
        return self._schedules.get_all_definitions()

    def get_schedule(self, schedule_name: str) -> ScheduleDefinition:
        """Get a schedule by name.

        if this schedule has not yet been constructed, only this schedule is constructed, and will
        be cached for future calls.

        args:
            schedule_name (str): name of the schedule to retrieve.

        Returns:
            ScheduleDefinition: The schedule definition corresponding to the given name.
        """
        check.str_param(schedule_name, "schedule_name")

        return self._schedules.get_definition(schedule_name)

    def has_schedule(self, schedule_name: str) -> bool:
        check.str_param(schedule_name, "schedule_name")

        return self._schedules.has_definition(schedule_name)

    def get_all_sensors(self) -> Sequence[SensorDefinition]:
        return self._sensors.get_all_definitions()

    def get_sensor_names(self) -> Sequence[str]:
        return self._sensors.get_definition_names()

    def get_sensor(self, sensor_name: str) -> SensorDefinition:
        return self._sensors.get_definition(sensor_name)

    def has_sensor(self, sensor_name: str) -> bool:
        return self._sensors.has_definition(sensor_name)

    def get_source_assets_by_key(self) -> Mapping[AssetKey, SourceAsset]:
        return self._source_assets_by_key

    def get_assets_defs_by_key(self) -> Mapping[AssetKey, "AssetsDefinition"]:
        return self._assets_defs_by_key

    def _check_solid_defs(self, pipelines: Sequence[PipelineDefinition]) -> None:
        solid_defs = {}
        solid_to_pipeline = {}
        for pipeline in pipelines:
            for solid_def in [*pipeline.all_node_defs, pipeline.graph]:
                # skip checks for subselected graphs because they don't have their own names
                if isinstance(solid_def, SubselectedGraphDefinition):
                    break

                if solid_def.name not in solid_defs:
                    solid_defs[solid_def.name] = solid_def
                    solid_to_pipeline[solid_def.name] = pipeline.name

                if solid_defs[solid_def.name] is not solid_def:
                    first_name, second_name = sorted(
                        [solid_to_pipeline[solid_def.name], pipeline.name]
                    )
                    raise DagsterInvalidDefinitionError(
                        f"Conflicting definitions found in repository with name '{solid_def.name}'."
                        " Op/Graph definition names must be unique within a repository."
                        f" {solid_def.__class__.__name__} is defined in"
                        f" {pipeline.target_type} '{first_name}' and in"
                        f" {pipeline.target_type} '{second_name}'."
                    )

    def _validate_pipeline(self, pipeline: PipelineDefinition) -> PipelineDefinition:
        return pipeline

    def _validate_job(self, job: JobDefinition) -> JobDefinition:
        return job

    def _validate_schedule(self, schedule: ScheduleDefinition) -> ScheduleDefinition:
        pipelines = self.get_pipeline_names()

        if schedule.job_name not in pipelines:
            raise DagsterInvalidDefinitionError(
                f'ScheduleDefinition "{schedule.name}" targets job/pipeline "{schedule.job_name}" '
                "which was not found in this repository."
            )

        return schedule

    def _validate_sensor(self, sensor: SensorDefinition) -> SensorDefinition:
        pipelines = self.get_pipeline_names()
        if len(sensor.targets) == 0:
            # skip validation when the sensor does not target a pipeline
            return sensor

        for target in sensor.targets:
            if target.pipeline_name not in pipelines:
                raise DagsterInvalidDefinitionError(
                    f'SensorDefinition "{sensor.name}" targets job/pipeline "{sensor.job_name}" '
                    "which was not found in this repository."
                )

        return sensor

    def _validate_partition_set(
        self, partition_set: PartitionSetDefinition
    ) -> PartitionSetDefinition:
        return partition_set


class RepositoryDefinition:
    """Define a repository that contains a group of definitions.

    Users should typically not create objects of this class directly. Instead, use the
    :py:func:`@repository` decorator.

    Args:
        name (str): The name of the repository.
        repository_data (RepositoryData): Contains the definitions making up the repository.
        description (Optional[str]): A string description of the repository.
    """

    def __init__(
        self,
        name,
        *,
        repository_data,
        description=None,
        repository_load_data=None,
    ):
        self._name = check_valid_name(name)
        self._description = check.opt_str_param(description, "description")
        self._repository_data = check.inst_param(repository_data, "repository_data", RepositoryData)
        self._repository_load_data = check.opt_inst_param(
            repository_load_data, "repository_load_data", RepositoryLoadData
        )

    @property
    def repository_load_data(self) -> Optional[RepositoryLoadData]:
        return self._repository_load_data

    @public  # type: ignore
    @property
    def name(self) -> str:
        return self._name

    @public  # type: ignore
    @property
    def description(self) -> Optional[str]:
        return self._description

    def load_all_definitions(self):
        # force load of all lazy constructed code artifacts
        self._repository_data.load_all_definitions()

    @property
    def pipeline_names(self) -> Sequence[str]:
        """List[str]: Names of all pipelines/jobs in the repository."""
        return self._repository_data.get_pipeline_names()

    @public  # type: ignore
    @property
    def job_names(self) -> Sequence[str]:
        """List[str]: Names of all jobs in the repository."""
        return self._repository_data.get_job_names()

    def has_pipeline(self, name: str) -> bool:
        """Check if a pipeline/job with a given name is present in the repository.

        Args:
            name (str): The name of the pipeline/job.

        Returns:
            bool
        """
        return self._repository_data.has_pipeline(name)

    def get_pipeline(self, name: str) -> PipelineDefinition:
        """Get a pipeline/job by name.

        If this pipeline/job is present in the lazily evaluated dictionary passed to the
        constructor, but has not yet been constructed, only this pipeline/job is constructed, and will
        be cached for future calls.

        Args:
            name (str): Name of the pipeline/job to retrieve.

        Returns:
            PipelineDefinition: The pipeline/job definition corresponding to the given name.
        """
        return self._repository_data.get_pipeline(name)

    def get_all_pipelines(self) -> Sequence[PipelineDefinition]:
        """Return all pipelines/jobs in the repository as a list.

        Note that this will construct any pipeline/job in the lazily evaluated dictionary that
        has not yet been constructed.

        Returns:
            List[PipelineDefinition]: All pipelines/jobs in the repository.
        """
        return self._repository_data.get_all_pipelines()

    @public  # type: ignore
    def has_job(self, name: str) -> bool:
        """Check if a job with a given name is present in the repository.

        Args:
            name (str): The name of the job.

        Returns:
            bool
        """
        return self._repository_data.has_job(name)

    @public  # type: ignore
    def get_job(self, name: str) -> JobDefinition:
        """Get a job by name.

        If this job is present in the lazily evaluated dictionary passed to the
        constructor, but has not yet been constructed, only this job is constructed, and
        will be cached for future calls.

        Args:
            name (str): Name of the job to retrieve.

        Returns:
            JobDefinition: The job definition corresponding to
            the given name.
        """
        return self._repository_data.get_job(name)

    @public
    def get_all_jobs(self) -> Sequence[JobDefinition]:
        """Return all jobs in the repository as a list.

        Note that this will construct any job in the lazily evaluated dictionary that has
        not yet been constructed.

        Returns:
            List[JobDefinition]: All jobs in the repository.
        """
        return self._repository_data.get_all_jobs()

    @property
    def partition_set_defs(self) -> Sequence[PartitionSetDefinition]:
        return self._repository_data.get_all_partition_sets()

    def get_partition_set_def(self, name: str) -> PartitionSetDefinition:
        return self._repository_data.get_partition_set(name)

    @public  # type: ignore
    @property
    def schedule_defs(self) -> Sequence[ScheduleDefinition]:
        return self._repository_data.get_all_schedules()

    @public  # type: ignore
    def get_schedule_def(self, name: str) -> ScheduleDefinition:
        return self._repository_data.get_schedule(name)

    @public  # type: ignore
    def has_schedule_def(self, name: str) -> bool:
        return self._repository_data.has_schedule(name)

    @public  # type: ignore
    @property
    def sensor_defs(self) -> Sequence[SensorDefinition]:
        return self._repository_data.get_all_sensors()

    @public  # type: ignore
    def get_sensor_def(self, name: str) -> SensorDefinition:
        return self._repository_data.get_sensor(name)

    @public  # type: ignore
    def has_sensor_def(self, name: str) -> bool:
        return self._repository_data.has_sensor(name)

    @property
    def source_assets_by_key(self) -> Mapping[AssetKey, SourceAsset]:
        return self._repository_data.get_source_assets_by_key()

    @property
    def _assets_defs_by_key(self) -> Mapping[AssetKey, "AssetsDefinition"]:
        return self._repository_data.get_assets_defs_by_key()

    def has_implicit_global_asset_job_def(self) -> bool:
        """Returns true is there is a single implicit asset job for all asset keys in a repository.
        """
        return self.has_job(ASSET_BASE_JOB_PREFIX)

    def get_implicit_global_asset_job_def(self) -> JobDefinition:
        """A useful conveninence method for repositories where there are a set of assets with
        the same partitioning schema and one wants to access their corresponding implicit job
        easily.
        """
        if not self.has_job(ASSET_BASE_JOB_PREFIX):
            raise DagsterInvariantViolationError(
                "There is no single global asset job, likely due to assets using "
                "different partitioning schemes via their partitions_def parameter. You must "
                "use get_implicit_job_def_for_assets in order to access the correct implicit job."
            )

        return self.get_job(ASSET_BASE_JOB_PREFIX)

    def get_implicit_asset_job_names(self) -> Sequence[str]:
        return [
            job_name for job_name in self.job_names if job_name.startswith(ASSET_BASE_JOB_PREFIX)
        ]

    def get_implicit_job_def_for_assets(
        self, asset_keys: Iterable[AssetKey]
    ) -> Optional[JobDefinition]:
        """
        Returns the asset base job that contains all the given assets, or None if there is no such
        job.
        """
        if self.has_job(ASSET_BASE_JOB_PREFIX):
            base_job = self.get_job(ASSET_BASE_JOB_PREFIX)
            if all(key in base_job.asset_layer.assets_defs_by_key for key in asset_keys):
                return base_job
        else:
            i = 0
            while self.has_job(f"{ASSET_BASE_JOB_PREFIX}_{i}"):
                base_job = self.get_job(f"{ASSET_BASE_JOB_PREFIX}_{i}")
                if all(key in base_job.asset_layer.assets_defs_by_key for key in asset_keys):
                    return base_job

                i += 1

        return None

    def get_maybe_subset_job_def(
        self,
        job_name: str,
        op_selection: Optional[Sequence[str]] = None,
        asset_selection: Optional[AbstractSet[AssetKey]] = None,
        solids_to_execute: Optional[AbstractSet[str]] = None,
    ):
        # named job forward expecting pipeline distinction to be removed soon
        defn = self.get_pipeline(job_name)
        if isinstance(defn, JobDefinition):
            return defn.get_job_def_for_subset_selection(op_selection, asset_selection)

        check.invariant(
            asset_selection is None,
            f"Asset selection cannot be provided with a pipeline {asset_selection}",
        )
        # pipelines use post-resolved selection, should be removed soon
        if op_selection and solids_to_execute is None:
            solids_to_execute = parse_solid_selection(defn, op_selection)

        return defn.get_pipeline_subset_def(solids_to_execute)

    @public
    def load_asset_value(
        self,
        asset_key: CoercibleToAssetKey,
        *,
        python_type: Optional[Type] = None,
        instance: Optional[DagsterInstance] = None,
        partition_key: Optional[str] = None,
    ) -> object:
        """
        Load the contents of an asset as a Python object.

        Invokes `load_input` on the :py:class:`IOManager` associated with the asset.

        If you want to load the values of multiple assets, it's more efficient to use
        :py:meth:`~dagster.RepositoryDefinition.get_asset_value_loader`, which avoids spinning up
        resources separately for each asset.

        Args:
            asset_key (Union[AssetKey, Sequence[str], str]): The key of the asset to load.
            python_type (Optional[Type]): The python type to load the asset as. This is what will
                be returned inside `load_input` by `context.dagster_type.typing_type`.
            partition_key (Optional[str]): The partition of the asset to load.

        Returns:
            The contents of an asset as a Python object.
        """
        from dagster._core.storage.asset_value_loader import AssetValueLoader

        with AssetValueLoader(self._assets_defs_by_key, instance=instance) as loader:
            return loader.load_asset_value(
                asset_key, python_type=python_type, partition_key=partition_key
            )

    @public
    def get_asset_value_loader(
        self, instance: Optional[DagsterInstance] = None
    ) -> "AssetValueLoader":
        """
        Returns an object that can load the contents of assets as Python objects.

        Invokes `load_input` on the :py:class:`IOManager` associated with the assets. Avoids
        spinning up resources separately for each asset.

        Usage:

        .. code-block:: python

            with my_repo.get_asset_value_loader() as loader:
                asset1 = loader.load_asset_value("asset1")
                asset2 = loader.load_asset_value("asset2")

        """
        from dagster._core.storage.asset_value_loader import AssetValueLoader

        return AssetValueLoader(self._assets_defs_by_key, instance=instance)

    @property
    def asset_graph(self) -> AssetGraph:
        return AssetGraph.from_assets(
            [*set(self._assets_defs_by_key.values()), *self.source_assets_by_key.values()]
        )

    # If definition comes from the @repository decorator, then the __call__ method will be
    # overwritten. Therefore, we want to maintain the call-ability of repository definitions.
    def __call__(self, *args, **kwargs):
        return self


class PendingRepositoryDefinition:
    def __init__(
        self,
        name: str,
        repository_definitions: Sequence[
            Union[RepositoryListDefinition, "CacheableAssetsDefinition"]
        ],
        description: Optional[str] = None,
        default_logger_defs: Optional[Mapping[str, LoggerDefinition]] = None,
        default_executor_def: Optional[ExecutorDefinition] = None,
    ):
        self._repository_definitions = check.list_param(
            repository_definitions,
            "repository_definition",
            additional_message=(
                "PendingRepositoryDefinition supports only list-based repository data at this time."
            ),
        )
        self._name = name
        self._description = description
        self._default_logger_defs = default_logger_defs
        self._default_executor_def = default_executor_def

    @property
    def name(self) -> str:
        return self._name

    def _compute_repository_load_data(self) -> RepositoryLoadData:
        from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition

        return RepositoryLoadData(
            cached_data_by_key={
                defn.unique_id: defn.compute_cacheable_data()
                for defn in self._repository_definitions
                if isinstance(defn, CacheableAssetsDefinition)
            }
        )

    def _get_repository_definition(
        self, repository_load_data: RepositoryLoadData
    ) -> RepositoryDefinition:
        from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition

        resolved_definitions: List[RepositoryListDefinition] = []
        for defn in self._repository_definitions:
            if isinstance(defn, CacheableAssetsDefinition):
                # should always have metadata for each cached defn at this point
                check.invariant(
                    defn.unique_id in repository_load_data.cached_data_by_key,
                    (
                        "No metadata found for CacheableAssetsDefinition with unique_id"
                        f" {defn.unique_id}."
                    ),
                )
                # use the emtadata to generate definitions
                resolved_definitions.extend(
                    defn.build_definitions(
                        data=repository_load_data.cached_data_by_key[defn.unique_id]
                    )
                )
            else:
                resolved_definitions.append(defn)

        repository_data = CachingRepositoryData.from_list(
            resolved_definitions,
            default_executor_def=self._default_executor_def,
            default_logger_defs=self._default_logger_defs,
        )

        return RepositoryDefinition(
            self._name,
            repository_data=repository_data,
            description=self._description,
            repository_load_data=repository_load_data,
        )

    def reconstruct_repository_definition(
        self, repository_load_data: RepositoryLoadData
    ) -> RepositoryDefinition:
        """Use the provided RepositoryLoadData to construct and return a RepositoryDefinition."""
        check.inst_param(repository_load_data, "repository_load_data", RepositoryLoadData)
        return self._get_repository_definition(repository_load_data)

    def compute_repository_definition(self) -> RepositoryDefinition:
        """Compute the required RepositoryLoadData and use it to construct and return a RepositoryDefinition.
        """
        repository_load_data = self._compute_repository_load_data()
        return self._get_repository_definition(repository_load_data)


def _process_and_validate_target(
    schedule_or_sensor_def: Union[SensorDefinition, ScheduleDefinition],
    coerced_graphs: Dict[str, JobDefinition],
    unresolved_jobs: Dict[str, UnresolvedAssetJobDefinition],
    pipelines_or_jobs: Dict[str, PipelineDefinition],
    target: Union[GraphDefinition, PipelineDefinition, UnresolvedAssetJobDefinition],
):
    # This function modifies the state of coerced_graphs and unresolved_jobs
    targeter = (
        f"schedule '{schedule_or_sensor_def.name}'"
        if isinstance(schedule_or_sensor_def, ScheduleDefinition)
        else f"sensor '{schedule_or_sensor_def.name}'"
    )
    if isinstance(target, GraphDefinition):
        if target.name not in coerced_graphs:
            # Since this is a graph we have to coerce, it is not possible to be
            # the same definition by reference equality
            if target.name in pipelines_or_jobs:
                dupe_target_type = pipelines_or_jobs[target.name].target_type
                raise DagsterInvalidDefinitionError(
                    _get_error_msg_for_target_conflict(
                        targeter, "graph", target.name, dupe_target_type
                    )
                )
        elif coerced_graphs[target.name].graph != target:
            raise DagsterInvalidDefinitionError(
                _get_error_msg_for_target_conflict(targeter, "graph", target.name, "graph")
            )
        coerced_job = target.coerce_to_job()
        coerced_graphs[target.name] = coerced_job
        pipelines_or_jobs[target.name] = coerced_job
    elif isinstance(target, UnresolvedAssetJobDefinition):
        if target.name not in unresolved_jobs:
            # Since this is am unresolved job we have to resolve, it is not possible to
            # be the same definition by reference equality
            if target.name in pipelines_or_jobs:
                dupe_target_type = pipelines_or_jobs[target.name].target_type
                raise DagsterInvalidDefinitionError(
                    _get_error_msg_for_target_conflict(
                        targeter, "unresolved asset job", target.name, dupe_target_type
                    )
                )
        elif unresolved_jobs[target.name].selection != target.selection:
            raise DagsterInvalidDefinitionError(
                _get_error_msg_for_target_conflict(
                    targeter, "unresolved asset job", target.name, "unresolved asset job"
                )
            )
        unresolved_jobs[target.name] = target
    else:
        if target.name in pipelines_or_jobs and pipelines_or_jobs[target.name] != target:
            dupe_target_type = (
                "graph"
                if target.name in coerced_graphs
                else "unresolved asset job"
                if target.name in unresolved_jobs
                else pipelines_or_jobs[target.name].target_type
            )
            raise DagsterInvalidDefinitionError(
                _get_error_msg_for_target_conflict(
                    targeter, target.target_type, target.name, dupe_target_type
                )
            )
        pipelines_or_jobs[target.name] = target


def _get_error_msg_for_target_conflict(targeter, target_type, target_name, dupe_target_type):
    return (
        f"{targeter} targets {target_type} '{target_name}', but a different {dupe_target_type} with"
        " the same name was provided. Disambiguate between these by providing a separate name to"
        " one of them."
    )


def _get_partition_set_from_schedule(
    schedule: ScheduleDefinition,
) -> Optional[PartitionSetDefinition]:
    """With the legacy APIs, partition sets can live on schedules. With the non-legacy APIs,
    they live on jobs. Pulling partition sets from schedules causes problems with unresolved asset
    jobs, because two different instances of the same logical partition set end up getting created
    - one on the schedule and one on the the resolved job.

    To avoid this problem, we avoid pulling partition sets off of schedules that target unresolved
    asset jobs. This works, because the partition set still gets pulled directly off the asset job
    elsewhere.

    When we remove the legacy APIs, we should be able to stop pulling partition sets off of
    schedules entirely and remove this entire code path.
    """
    if (
        isinstance(schedule, PartitionScheduleDefinition)
        and not schedule.targets_unresolved_asset_job
    ):
        return schedule.get_partition_set()
    else:
        return None
