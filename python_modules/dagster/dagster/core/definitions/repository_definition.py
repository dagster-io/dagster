import warnings
from abc import ABC, abstractmethod
from inspect import isfunction
from types import FunctionType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Mapping,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
)

import dagster._check as check
from dagster.core.asset_defs.source_asset import SourceAsset
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster.utils import merge_dicts

from .events import AssetKey
from .graph_definition import GraphDefinition, SubselectedGraphDefinition
from .job_definition import JobDefinition
from .partition import PartitionScheduleDefinition, PartitionSetDefinition
from .pipeline_definition import PipelineDefinition
from .schedule_definition import ScheduleDefinition
from .sensor_definition import SensorDefinition
from .utils import check_valid_name

if TYPE_CHECKING:
    from dagster.core.asset_defs.asset_group import AssetGroup

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
        lazy_definitions_fn: Optional[Callable[[], List[RepositoryLevelDefinition]]] = None,
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
        self._definition_names: Optional[List[str]] = None

        self._lazy_definitions_fn: Callable[
            [], List[RepositoryLevelDefinition]
        ] = lazy_definitions_fn or (lambda: [])
        self._lazy_definitions: Optional[List[RepositoryLevelDefinition]] = None

        self._all_definitions: Optional[List[RepositoryLevelDefinition]] = None

    def _get_lazy_definitions(self) -> List[RepositoryLevelDefinition]:
        if self._lazy_definitions is None:
            self._lazy_definitions = self._lazy_definitions_fn()
            for definition in self._lazy_definitions:
                self._validate_and_cache_definition(definition, definition.name)

        return self._lazy_definitions

    def get_definition_names(self) -> List[str]:
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

    def get_all_definitions(self) -> List[RepositoryLevelDefinition]:
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
    def get_all_pipelines(self) -> List[PipelineDefinition]:
        """Return all pipelines/jobs in the repository as a list.

        Returns:
            List[PipelineDefinition]: All pipelines/jobs in the repository.
        """

    def get_all_jobs(self) -> List[JobDefinition]:
        """Return all jobs in the repository as a list.

        Returns:
            List[JobDefinition]: All jobs in the repository.
        """
        return [job for job in self.get_all_pipelines() if isinstance(job, JobDefinition)]

    def get_pipeline_names(self) -> List[str]:
        """Get the names of all pipelines/jobs in the repository.

        Returns:
            List[str]
        """
        return [pipeline_def.name for pipeline_def in self.get_all_pipelines()]

    def get_job_names(self) -> List[str]:
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

    def get_all_partition_sets(self) -> List[PartitionSetDefinition]:
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

    def get_schedule_names(self) -> List[str]:
        """Get the names of all schedules in the repository.

        Returns:
            List[str]
        """
        return [schedule.name for schedule in self.get_all_schedules()]

    def get_all_schedules(self) -> List[ScheduleDefinition]:
        """Return all schedules in the repository as a list.

        Returns:
            List[ScheduleDefinition]: All pipelines in the repository.
        """
        return []

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

    def get_all_sensors(self) -> List[SensorDefinition]:
        return []

    def get_sensor_names(self) -> List[str]:
        return [sensor.name for sensor in self.get_all_sensors()]

    def get_sensor(self, sensor_name: str) -> SensorDefinition:
        sensors_with_name = [
            sensor for sensor in self.get_all_sensors() if sensor.name == sensor_name
        ]
        if not sensors_with_name:
            raise DagsterInvariantViolationError(
                f"Could not find sensor {sensor_name} in repository"
            )
        return sensors_with_name[0]

    def has_sensor(self, sensor_name: str) -> bool:
        return sensor_name in self.get_sensor_names()

    def get_source_assets_by_key(self) -> Mapping[AssetKey, SourceAsset]:
        return {}


T = TypeVar("T")
Resolvable = Callable[[], T]


class CachingRepositoryData(RepositoryData):
    """Default implementation of RepositoryData used by the :py:func:`@repository <repository>` decorator."""

    _all_jobs: Optional[List[JobDefinition]]
    _all_pipelines: Optional[List[PipelineDefinition]]

    def __init__(
        self,
        pipelines: Mapping[str, Union[PipelineDefinition, Resolvable[PipelineDefinition]]],
        jobs: Mapping[str, Union[JobDefinition, Resolvable[JobDefinition]]],
        partition_sets: Mapping[
            str, Union[PartitionSetDefinition, Resolvable[PartitionSetDefinition]]
        ],
        schedules: Mapping[str, Union[ScheduleDefinition, Resolvable[ScheduleDefinition]]],
        sensors: Mapping[str, Union[SensorDefinition, Resolvable[SensorDefinition]]],
        source_assets: Mapping[AssetKey, SourceAsset],
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
            source_assets (Mapping[AssetKey, SourceAsset]): The source assets belonging to a repository.
        """
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
            source_assets, "source_assets", key_type=AssetKey, value_type=SourceAsset
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
        schedule_partition_sets = [
            schedule.get_partition_set()
            for schedule in self._schedules.get_all_definitions()
            if isinstance(schedule, PartitionScheduleDefinition)
        ]
        self._source_assets = source_assets

        def load_partition_sets_from_pipelines() -> List[PartitionSetDefinition]:
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
                f"Duplicate definitions between schedules and sensors found for keys: {', '.join(duplicate_keys)}"
            )

        # merge jobs in to pipelines while they are just implemented as pipelines
        for key, job in repository_definitions["jobs"].items():
            if key in repository_definitions["pipelines"]:
                raise DagsterInvalidDefinitionError(
                    f'Conflicting entries for name {key} in "jobs" and "pipelines".'
                )

            if isinstance(job, GraphDefinition):
                repository_definitions["jobs"][key] = job.coerce_to_job()
            elif not isinstance(job, JobDefinition) and not isfunction(job):
                raise DagsterInvalidDefinitionError(
                    f"Object mapped to {key} is not an instance of JobDefinition or GraphDefinition."
                )

        return CachingRepositoryData(**repository_definitions, source_assets={})

    @classmethod
    def from_list(
        cls,
        repository_definitions: List[
            Union[
                PipelineDefinition,
                PartitionSetDefinition,
                ScheduleDefinition,
                SensorDefinition,
                "AssetGroup",
                GraphDefinition,
            ]
        ],
    ) -> "CachingRepositoryData":
        """Static constructor.

        Args:
            repository_definitions (List[Union[PipelineDefinition, PartitionSetDefinition, ScheduleDefinition, SensorDefinition, AssetGroup, GraphDefinition]]):
                Use this constructor when you have no need to lazy load pipelines/jobs or other
                definitions.
        """
        from dagster.core.asset_defs import AssetGroup

        pipelines_or_jobs: Dict[str, Union[PipelineDefinition, JobDefinition]] = {}
        coerced_graphs: Dict[str, JobDefinition] = {}
        partition_sets: Dict[str, PartitionSetDefinition] = {}
        schedules: Dict[str, ScheduleDefinition] = {}
        sensors: Dict[str, SensorDefinition] = {}
        source_assets: Dict[AssetKey, SourceAsset] = {}
        combined_asset_group = None
        for definition in repository_definitions:
            if isinstance(definition, PipelineDefinition):
                if (
                    definition.name in pipelines_or_jobs
                    and pipelines_or_jobs[definition.name] != definition
                ):
                    raise DagsterInvalidDefinitionError(
                        "Duplicate {target_type} definition found for {target}".format(
                            target_type=definition.target_type, target=definition.describe_target()
                        )
                    )
                if AssetGroup.is_base_job_name(definition.name):
                    raise DagsterInvalidDefinitionError(
                        f"Attempted to provide job called {definition.name} to repository, which "
                        "is a reserved name. Please rename the job."
                    )
                pipelines_or_jobs[definition.name] = definition
            elif isinstance(definition, PartitionSetDefinition):
                if definition.name in partition_sets:
                    raise DagsterInvalidDefinitionError(
                        "Duplicate partition set definition found for partition set "
                        "{partition_set_name}".format(partition_set_name=definition.name)
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
                if isinstance(definition, PartitionScheduleDefinition):
                    partition_set_def = definition.get_partition_set()
                    if (
                        partition_set_def.name in partition_sets
                        and partition_set_def != partition_sets[partition_set_def.name]
                    ):
                        raise DagsterInvalidDefinitionError(
                            "Duplicate partition set definition found for partition set "
                            "{partition_set_name}".format(partition_set_name=partition_set_def.name)
                        )
                    partition_sets[partition_set_def.name] = partition_set_def
            elif isinstance(definition, GraphDefinition):
                coerced = definition.coerce_to_job()
                if coerced.name in pipelines_or_jobs:
                    raise DagsterInvalidDefinitionError(
                        "Duplicate {target_type} definition found for graph '{name}'".format(
                            target_type=coerced.target_type, name=coerced.name
                        )
                    )
                pipelines_or_jobs[coerced.name] = coerced
                coerced_graphs[coerced.name] = coerced

            elif isinstance(definition, AssetGroup):
                if combined_asset_group:
                    combined_asset_group += definition
                else:
                    combined_asset_group = definition
            else:
                check.failed(f"Unexpected repository entry {definition}")

        if combined_asset_group:
            for job_def in combined_asset_group.get_base_jobs():
                pipelines_or_jobs[job_def.name] = job_def

            source_assets = {
                source_asset.key: source_asset
                for source_asset in combined_asset_group.source_assets
            }

        for name, sensor_def in sensors.items():
            if sensor_def.has_loadable_targets():
                targets = sensor_def.load_targets()
                for target in targets:
                    _process_and_validate_target(
                        sensor_def, coerced_graphs, pipelines_or_jobs, target
                    )

        for name, schedule_def in schedules.items():
            if schedule_def.has_loadable_target():
                target = schedule_def.load_target()
                _process_and_validate_target(
                    schedule_def, coerced_graphs, pipelines_or_jobs, target
                )

        pipelines: Dict[str, PipelineDefinition] = {}
        jobs: Dict[str, JobDefinition] = {}
        for name, pipeline_or_job in pipelines_or_jobs.items():
            if isinstance(pipeline_or_job, JobDefinition):
                jobs[name] = pipeline_or_job
            else:
                pipelines[name] = pipeline_or_job

        return CachingRepositoryData(
            pipelines=pipelines,
            jobs=jobs,
            partition_sets=partition_sets,
            schedules=schedules,
            sensors=sensors,
            source_assets=source_assets,
        )

    def get_pipeline_names(self) -> List[str]:
        """Get the names of all pipelines/jobs in the repository.

        Returns:
            List[str]
        """
        return self._pipelines.get_definition_names() + self.get_job_names()

    def get_job_names(self) -> List[str]:
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

    def get_all_pipelines(self) -> List[PipelineDefinition]:
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

    def get_all_jobs(self) -> List[JobDefinition]:
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
        return cast(List[JobDefinition], self._all_jobs)

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

    def get_partition_set_names(self) -> List[str]:
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

    def get_all_partition_sets(self) -> List[PartitionSetDefinition]:
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

    def get_schedule_names(self) -> List[str]:
        """Get the names of all schedules in the repository.

        Returns:
            List[str]
        """
        return self._schedules.get_definition_names()

    def get_all_schedules(self) -> List[ScheduleDefinition]:
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

    def get_all_sensors(self) -> List[SensorDefinition]:
        return self._sensors.get_all_definitions()

    def get_sensor_names(self) -> List[str]:
        return self._sensors.get_definition_names()

    def get_sensor(self, sensor_name: str) -> SensorDefinition:
        return self._sensors.get_definition(sensor_name)

    def has_sensor(self, sensor_name: str) -> bool:
        return self._sensors.has_definition(sensor_name)

    def get_source_assets_by_key(self) -> Mapping[AssetKey, SourceAsset]:
        return self._source_assets

    def _check_solid_defs(self, pipelines: List[PipelineDefinition]) -> None:
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

                if not solid_defs[solid_def.name] is solid_def:
                    first_name, second_name = sorted(
                        [solid_to_pipeline[solid_def.name], pipeline.name]
                    )
                    raise DagsterInvalidDefinitionError(
                        (
                            f"Conflicting definitions found in repository with name '{solid_def.name}'. "
                            "Op/Graph/Solid definition names must be unique within a "
                            f"repository. {solid_def.__class__.__name__} is defined in {pipeline.target_type} "
                            f"'{first_name}' and in {pipeline.target_type} '{second_name}'."
                        )
                    )

    def _validate_pipeline(self, pipeline: PipelineDefinition) -> PipelineDefinition:
        return pipeline

    def _validate_job(self, job: JobDefinition) -> JobDefinition:
        return job

    def _validate_schedule(self, schedule: ScheduleDefinition) -> ScheduleDefinition:
        pipelines = self.get_pipeline_names()

        if schedule.pipeline_name not in pipelines:
            raise DagsterInvalidDefinitionError(
                f'ScheduleDefinition "{schedule.name}" targets job/pipeline "{schedule.pipeline_name}" '
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
                    f'SensorDefinition "{sensor.name}" targets job/pipeline "{sensor.pipeline_name}" '
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
        repository_data,
        description=None,
    ):
        self._name = check_valid_name(name)
        self._description = check.opt_str_param(description, "description")
        self._repository_data = check.inst_param(repository_data, "repository_data", RepositoryData)

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> Optional[str]:
        return self._description

    @property
    def pipeline_names(self) -> List[str]:
        """List[str]: Names of all pipelines/jobs in the repository"""
        return self._repository_data.get_pipeline_names()

    @property
    def job_names(self) -> List[str]:
        """List[str]: Names of all jobs in the repository"""
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

    def get_all_pipelines(self) -> List[PipelineDefinition]:
        """Return all pipelines/jobs in the repository as a list.

        Note that this will construct any pipeline/job in the lazily evaluated dictionary that
        has not yet been constructed.

        Returns:
            List[PipelineDefinition]: All pipelines/jobs in the repository.
        """
        return self._repository_data.get_all_pipelines()

    def has_job(self, name: str) -> bool:
        """Check if a job with a given name is present in the repository.

        Args:
            name (str): The name of the job.

        Returns:
            bool
        """
        return self._repository_data.has_job(name)

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

    def get_all_jobs(self) -> List[JobDefinition]:
        """Return all jobs in the repository as a list.

        Note that this will construct any job in the lazily evaluated dictionary that has
        not yet been constructed.

        Returns:
            List[JobDefinition]: All jobs in the repository.
        """
        return self._repository_data.get_all_jobs()

    @property
    def partition_set_defs(self) -> List[PartitionSetDefinition]:
        return self._repository_data.get_all_partition_sets()

    def get_partition_set_def(self, name: str) -> PartitionSetDefinition:
        return self._repository_data.get_partition_set(name)

    @property
    def schedule_defs(self) -> List[ScheduleDefinition]:
        return self._repository_data.get_all_schedules()

    def get_schedule_def(self, name: str) -> ScheduleDefinition:
        return self._repository_data.get_schedule(name)

    def has_schedule_def(self, name: str) -> bool:
        return self._repository_data.has_schedule(name)

    @property
    def sensor_defs(self) -> List[SensorDefinition]:
        return self._repository_data.get_all_sensors()

    def get_sensor_def(self, name: str) -> SensorDefinition:
        return self._repository_data.get_sensor(name)

    def has_sensor_def(self, name: str) -> bool:
        return self._repository_data.has_sensor(name)

    @property
    def source_assets_by_key(self) -> Dict[AssetKey, SourceAsset]:
        return self._repository_data.get_source_assets_by_key()

    # If definition comes from the @repository decorator, then the __call__ method will be
    # overwritten. Therefore, we want to maintain the call-ability of repository definitions.
    def __call__(self, *args, **kwargs):
        return self


def _process_and_validate_target(
    schedule_or_sensor_def: Union[SensorDefinition, ScheduleDefinition],
    coerced_graphs: Dict[str, JobDefinition],
    pipelines_or_jobs: Dict[str, PipelineDefinition],
    target: Union[GraphDefinition, PipelineDefinition],
):
    # This function modifies the state of coerced_graphs.
    targeter = (
        f"schedule '{schedule_or_sensor_def.name}'"
        if isinstance(schedule_or_sensor_def, ScheduleDefinition)
        else f"sensor '{schedule_or_sensor_def.name}'"
    )
    if isinstance(target, GraphDefinition):
        if target.name not in coerced_graphs:
            # Since this is a graph we have to coerce, is not possible to be
            # the same definition by reference equality
            if target.name in pipelines_or_jobs:
                dupe_target_type = pipelines_or_jobs[target.name].target_type
                warnings.warn(
                    _get_error_msg_for_target_conflict(
                        targeter, "graph", target.name, dupe_target_type
                    )
                )
        elif coerced_graphs[target.name].graph != target:
            warnings.warn(
                _get_error_msg_for_target_conflict(targeter, "graph", target.name, "graph")
            )
        coerced_job = target.coerce_to_job()
        coerced_graphs[target.name] = coerced_job
        pipelines_or_jobs[target.name] = coerced_job
    else:
        if target.name in pipelines_or_jobs and pipelines_or_jobs[target.name] != target:
            dupe_target_type = (
                pipelines_or_jobs[target.name].target_type
                if target.name not in coerced_graphs
                else "graph"
            )
            warnings.warn(
                _get_error_msg_for_target_conflict(
                    targeter, target.target_type, target.name, dupe_target_type
                )
            )
        pipelines_or_jobs[target.name] = target


def _get_error_msg_for_target_conflict(targeter, target_type, target_name, dupe_target_type):
    return f"{targeter} targets {target_type} '{target_name}', but a different {dupe_target_type} with the same name was provided. The {target_type} provided to {targeter} will override the existing {dupe_target_type}, but in Dagster 0.15.0, this will result in an error. Disambiguate between these by providing a separate name to one of them."
