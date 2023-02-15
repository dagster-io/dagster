from abc import ABC, abstractmethod
from types import FunctionType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    TypeVar,
    Union,
    cast,
)

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.executor_definition import ExecutorDefinition
from dagster._core.definitions.graph_definition import SubselectedGraphDefinition
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.logger_definition import LoggerDefinition
from dagster._core.definitions.partition import PartitionScheduleDefinition, PartitionSetDefinition
from dagster._core.definitions.pipeline_definition import PipelineDefinition
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.schedule_definition import ScheduleDefinition
from dagster._core.definitions.sensor_definition import SensorDefinition
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster._utils.merger import merge_dicts

from .caching_index import CacheingDefinitionIndex
from .valid_definitions import RepositoryListDefinition

if TYPE_CHECKING:
    from dagster._core.definitions import AssetsDefinition


T = TypeVar("T")
Resolvable = Callable[[], T]


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

    @abstractmethod
    def get_top_level_resources(self) -> Mapping[str, ResourceDefinition]:
        """
        Return all top-level resources in the repository as a list,
        such as those provided to the Definitions constructor.

        Returns:
            List[ResourceDefinition]: All top-level resources in the repository.
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

    @public
    def get_assets_defs_by_key(self) -> Mapping[AssetKey, "AssetsDefinition"]:
        return {}

    def load_all_definitions(self):
        # force load of all lazy constructed code artifacts
        self.get_all_pipelines()
        self.get_all_jobs()
        self.get_all_partition_sets()
        self.get_all_schedules()
        self.get_all_sensors()
        self.get_source_assets_by_key()


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
        top_level_resources: Mapping[str, ResourceDefinition],
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
            top_level_resources (Mapping[str, ResourceDefinition]): A dict of top-level
                resource keys to defintions, for resources which should be displayed in the UI.
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
        check.mapping_param(
            top_level_resources, "top_level_resources", key_type=str, value_type=ResourceDefinition
        )

        self._pipelines = CacheingDefinitionIndex(
            PipelineDefinition,
            "PipelineDefinition",
            "pipeline",
            pipelines,
            self._validate_pipeline,
        )

        self._jobs = CacheingDefinitionIndex(
            JobDefinition,
            "JobDefinition",
            "job",
            jobs,
            self._validate_job,
        )

        self._schedules = CacheingDefinitionIndex(
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
        self._top_level_resources = top_level_resources

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

        self._partition_sets = CacheingDefinitionIndex(
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
        self._sensors = CacheingDefinitionIndex(
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
        from .repository_data_builder import build_caching_repository_data_from_dict

        return build_caching_repository_data_from_dict(repository_definitions)

    @classmethod
    def from_list(
        cls,
        repository_definitions: Sequence[RepositoryListDefinition],
        default_executor_def: Optional[ExecutorDefinition] = None,
        default_logger_defs: Optional[Mapping[str, LoggerDefinition]] = None,
        top_level_resources: Optional[Mapping[str, ResourceDefinition]] = None,
    ) -> "CachingRepositoryData":
        """Static constructor.

        Args:
            repository_definitions (List[Union[PipelineDefinition, PartitionSetDefinition, ScheduleDefinition, SensorDefinition, AssetGroup, GraphDefinition]]):
                Use this constructor when you have no need to lazy load pipelines/jobs or other
                definitions.
            top_level_resources (Optional[Mapping[str, ResourceDefinition]]): A dict of top-level
                resource keys to defintions, for resources which should be displayed in the UI.
        """
        from .repository_data_builder import build_caching_repository_data_from_list

        return build_caching_repository_data_from_list(
            repository_definitions=repository_definitions,
            default_executor_def=default_executor_def,
            default_logger_defs=default_logger_defs,
            top_level_resources=top_level_resources,
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

    def get_top_level_resources(self) -> Mapping[str, ResourceDefinition]:
        return self._top_level_resources

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
