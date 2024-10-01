from abc import ABC, abstractmethod
from types import FunctionType
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    Dict,
    Mapping,
    Optional,
    Sequence,
    TypeVar,
    Union,
)

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.executor_definition import ExecutorDefinition
from dagster._core.definitions.graph_definition import SubselectedGraphDefinition
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.logger_definition import LoggerDefinition
from dagster._core.definitions.repository_definition.caching_index import CacheingDefinitionIndex
from dagster._core.definitions.repository_definition.valid_definitions import (
    RepositoryElementDefinition,
)
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.schedule_definition import ScheduleDefinition
from dagster._core.definitions.sensor_definition import SensorDefinition
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError

if TYPE_CHECKING:
    from dagster._core.definitions import AssetsDefinition
    from dagster._core.definitions.asset_checks import AssetChecksDefinition
    from dagster._core.definitions.partitioned_schedule import (
        UnresolvedPartitionedAssetScheduleDefinition,
    )

T = TypeVar("T")
Resolvable = Callable[[], T]


class RepositoryData(ABC):
    """Users should usually rely on the :py:func:`@repository <repository>` decorator to create new
    repositories, which will in turn call the static constructors on this class. However, users may
    subclass :py:class:`RepositoryData` for fine-grained control over access to and lazy creation
    of repository members.
    """

    @abstractmethod
    def get_top_level_resources(self) -> Mapping[str, ResourceDefinition]:
        """Return all top-level resources in the repository as a list,
        such as those provided to the Definitions constructor.

        Returns:
            List[ResourceDefinition]: All top-level resources in the repository.
        """

    @abstractmethod
    def get_env_vars_by_top_level_resource(self) -> Mapping[str, AbstractSet[str]]:
        pass

    @abstractmethod
    @public
    def get_all_jobs(self) -> Sequence[JobDefinition]:
        """Return all jobs in the repository as a list.

        Returns:
            List[JobDefinition]: All jobs in the repository.
        """

    @public
    def get_job_names(self) -> Sequence[str]:
        """Get the names of all jobs in the repository.

        Returns:
            List[str]
        """
        return [job_def.name for job_def in self.get_all_jobs()]

    @public
    def has_job(self, job_name: str) -> bool:
        """Check if a job with a given name is present in the repository.

        Args:
            job_name (str): The name of the job.

        Returns:
            bool
        """
        return job_name in self.get_job_names()

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
            List[ScheduleDefinition]: All jobs in the repository.
        """
        return []

    @public
    def get_schedule(self, schedule_name: str) -> ScheduleDefinition:
        """Get a schedule by name.

        Args:
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

    @public
    def has_schedule(self, schedule_name: str) -> bool:
        """Check if a schedule with a given name is present in the repository."""
        return schedule_name in self.get_schedule_names()

    @public
    def get_all_sensors(self) -> Sequence[SensorDefinition]:
        """Sequence[SensorDefinition]: Return all sensors in the repository as a list."""
        return []

    @public
    def get_sensor_names(self) -> Sequence[str]:
        """Sequence[str]: Get the names of all sensors in the repository."""
        return [sensor.name for sensor in self.get_all_sensors()]

    @public
    def get_sensor(self, sensor_name: str) -> SensorDefinition:
        """Get a sensor by name.

        Args:
            sensor_name (str): name of the sensor to retrieve.

        Returns:
            SensorDefinition: The sensor definition corresponding to the given name.
        """
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
        """Check if a sensor with a given name is present in the repository."""
        return sensor_name in self.get_sensor_names()

    @public
    def get_source_assets_by_key(self) -> Mapping[AssetKey, SourceAsset]:
        """Mapping[AssetKey, SourceAsset]: Get the source assets for the repository."""
        return {}

    @public
    def get_assets_defs_by_key(self) -> Mapping[AssetKey, "AssetsDefinition"]:
        """Mapping[AssetKey, AssetsDefinition]: Get the asset definitions for the repository."""
        return {}

    @public
    def get_asset_checks_defs_by_key(self) -> Mapping[AssetCheckKey, "AssetChecksDefinition"]:
        """Mapping[AssetCheckKey, AssetChecksDefinition]: Get the asset checks definitions for the repository."""
        return {}

    def load_all_definitions(self):
        # force load of all lazy constructed code artifacts
        self.get_all_jobs()
        self.get_all_schedules()
        self.get_all_sensors()
        self.get_source_assets_by_key()


class CachingRepositoryData(RepositoryData):
    """Default implementation of RepositoryData used by the :py:func:`@repository <repository>` decorator."""

    _all_jobs: Optional[Sequence[JobDefinition]]
    _all_pipelines: Optional[Sequence[JobDefinition]]

    def __init__(
        self,
        jobs: Mapping[str, Union[JobDefinition, Resolvable[JobDefinition]]],
        schedules: Mapping[str, Union[ScheduleDefinition, Resolvable[ScheduleDefinition]]],
        sensors: Mapping[str, Union[SensorDefinition, Resolvable[SensorDefinition]]],
        source_assets_by_key: Mapping[AssetKey, SourceAsset],
        assets_defs_by_key: Mapping[AssetKey, "AssetsDefinition"],
        asset_checks_defs_by_key: Mapping[AssetCheckKey, "AssetChecksDefinition"],
        top_level_resources: Mapping[str, ResourceDefinition],
        utilized_env_vars: Mapping[str, AbstractSet[str]],
        unresolved_partitioned_asset_schedules: Mapping[
            str, "UnresolvedPartitionedAssetScheduleDefinition"
        ],
    ):
        """Constructs a new CachingRepositoryData object.

        You may pass pipeline, job, and schedule definitions directly, or you may pass callables
        with no arguments that will be invoked to lazily construct definitions when accessed by
        name. This can be helpful for performance when there are many definitions in a repository,
        or when constructing the definitions is costly.

        Note that when lazily constructing a definition, the name of the definition must match its
        key in its dictionary index, or a :py:class:`DagsterInvariantViolationError` will be thrown
        at retrieval time.

        Args:
            jobs (Mapping[str, Union[JobDefinition, Callable[[], JobDefinition]]]):
                The job definitions belonging to the repository.
            schedules (Mapping[str, Union[ScheduleDefinition, Callable[[], ScheduleDefinition]]]):
                The schedules belonging to the repository.
            sensors (Mapping[str, Union[SensorDefinition, Callable[[], SensorDefinition]]]):
                The sensors belonging to a repository.
            source_assets_by_key (Mapping[AssetKey, SourceAsset]): The source assets belonging to a repository.
            assets_defs_by_key (Mapping[AssetKey, AssetsDefinition]): The assets definitions
                belonging to a repository.
            asset_checks_defs_by_key (Mapping[AssetKey, AssetChecksDefinition]): The asset checks definitions
                belonging to a repository.
            top_level_resources (Mapping[str, ResourceDefinition]): A dict of top-level
                resource keys to defintions, for resources which should be displayed in the UI.
        """
        from dagster._core.definitions import AssetsDefinition

        check.mapping_param(jobs, "jobs", key_type=str, value_type=(JobDefinition, FunctionType))
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
            asset_checks_defs_by_key,
            "assets_checks_defs_by_key",
            key_type=AssetCheckKey,
            value_type=AssetsDefinition,
        )
        check.mapping_param(
            top_level_resources, "top_level_resources", key_type=str, value_type=ResourceDefinition
        )
        check.mapping_param(
            utilized_env_vars,
            "utilized_resources",
            key_type=str,
        )

        self._jobs = CacheingDefinitionIndex(
            JobDefinition,
            "JobDefinition",
            "job",
            jobs,
            self._validate_job,
        )

        schedules = {
            **schedules,
            **{
                name: self._resolve_partitioned_asset_schedule_lambda(
                    unresolved_partitioned_asset_schedule
                )
                for name, unresolved_partitioned_asset_schedule in unresolved_partitioned_asset_schedules.items()
            },
        }

        self._schedules = CacheingDefinitionIndex(
            ScheduleDefinition,
            "ScheduleDefinition",
            "schedule",
            schedules,
            self._validate_schedule,
        )
        # load all schedules to force validation
        self._schedules.get_all_definitions()

        self._source_assets_by_key = source_assets_by_key
        self._assets_defs_by_key = assets_defs_by_key
        self._assets_checks_defs_by_key = asset_checks_defs_by_key
        self._top_level_resources = top_level_resources
        self._utilized_env_vars = utilized_env_vars

        self._sensors = CacheingDefinitionIndex(
            SensorDefinition,
            "SensorDefinition",
            "sensor",
            sensors,
            self._validate_sensor,
        )
        # load all sensors to force validation
        self._sensors.get_all_definitions()

        self._all_jobs = None

    def _resolve_partitioned_asset_schedule_lambda(
        self, unresolved_partitioned_asset_schedule: "UnresolvedPartitionedAssetScheduleDefinition"
    ) -> Callable[[], ScheduleDefinition]:
        def resolve_partitioned_asset_schedule() -> ScheduleDefinition:
            job = self.get_job(unresolved_partitioned_asset_schedule.job.name)
            return unresolved_partitioned_asset_schedule.resolve(job)

        return resolve_partitioned_asset_schedule

    @staticmethod
    def from_dict(repository_definitions: Dict[str, Dict[str, Any]]) -> "CachingRepositoryData":
        """Static constructor.

        Args:
            repository_definition (Dict[str, Dict[str, ...]]): A dict of the form:

                {
                    'jobs': Dict[str, Callable[[], JobDefinition]],
                    'schedules': Dict[str, Callable[[], ScheduleDefinition]]
                }

            This form is intended to allow definitions to be created lazily when accessed by name,
            which can be helpful for performance when there are many definitions in a repository, or
            when constructing the definitions is costly.
        """
        from dagster._core.definitions.repository_definition.repository_data_builder import (
            build_caching_repository_data_from_dict,
        )

        return build_caching_repository_data_from_dict(repository_definitions)

    @classmethod
    def from_list(
        cls,
        repository_definitions: Sequence[RepositoryElementDefinition],
        default_executor_def: Optional[ExecutorDefinition] = None,
        default_logger_defs: Optional[Mapping[str, LoggerDefinition]] = None,
        top_level_resources: Optional[Mapping[str, ResourceDefinition]] = None,
    ) -> "CachingRepositoryData":
        """Static constructor.

        Args:
            repository_definitions (List[Union[JobDefinition, ScheduleDefinition, SensorDefinition, GraphDefinition]]):
                Use this constructor when you have no need to lazy load jobs or other definitions.
            top_level_resources (Optional[Mapping[str, ResourceDefinition]]): A dict of top-level
                resource keys to defintions, for resources which should be displayed in the UI.
        """
        from dagster._core.definitions.repository_definition.repository_data_builder import (
            build_caching_repository_data_from_list,
        )

        return build_caching_repository_data_from_list(
            repository_definitions=repository_definitions,
            default_executor_def=default_executor_def,
            default_logger_defs=default_logger_defs,
            top_level_resources=top_level_resources,
        )

    def get_env_vars_by_top_level_resource(self) -> Mapping[str, AbstractSet[str]]:
        return self._utilized_env_vars

    def get_job_names(self) -> Sequence[str]:
        """Get the names of all jobs in the repository.

        Returns:
            List[str]
        """
        return self._jobs.get_definition_names()

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

    def get_all_jobs(self) -> Sequence[JobDefinition]:
        """Return all jobs in the repository as a list.

        Note that this will construct any job that has not yet been constructed.

        Returns:
            List[JobDefinition]: All jobs in the repository.
        """
        if self._all_jobs is not None:
            return self._all_jobs

        self._all_jobs = self._jobs.get_all_definitions()
        self._check_node_defs(self._all_jobs)
        return self._all_jobs

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

        Args:
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

    def get_asset_checks_defs_by_key(self) -> Mapping[AssetCheckKey, "AssetChecksDefinition"]:
        return self._assets_checks_defs_by_key

    def _check_node_defs(self, job_defs: Sequence[JobDefinition]) -> None:
        node_defs = {}
        node_to_job = {}
        for job_def in job_defs:
            for node_def in [*job_def.all_node_defs, job_def.graph]:
                # skip checks for subselected graphs because they don't have their own names
                if isinstance(node_def, SubselectedGraphDefinition):
                    break

                if node_def.name not in node_defs:
                    node_defs[node_def.name] = node_def
                    node_to_job[node_def.name] = job_def.name

                if node_defs[node_def.name] is not node_def:
                    first_name, second_name = sorted([node_to_job[node_def.name], job_def.name])
                    raise DagsterInvalidDefinitionError(
                        f"Conflicting definitions found in repository with name '{node_def.name}'."
                        " Op/Graph definition names must be unique within a repository."
                        f" {node_def.__class__.__name__} is defined in"
                        f" job '{first_name}' and in"
                        f" job '{second_name}'."
                    )

    def _validate_job(self, job: JobDefinition) -> JobDefinition:
        return job

    def _validate_schedule(self, schedule: ScheduleDefinition) -> ScheduleDefinition:
        job_names = self.get_job_names()

        if schedule.job_name not in job_names:
            raise DagsterInvalidDefinitionError(
                f'ScheduleDefinition "{schedule.name}" targets job "{schedule.job_name}" '
                "which was not found in this repository."
            )

        return schedule

    def _validate_sensor(self, sensor: SensorDefinition) -> SensorDefinition:
        job_names = self.get_job_names()
        if len(sensor.targets) == 0:
            # skip validation when the sensor does not target a job
            return sensor

        for target in sensor.targets:
            if target.job_name not in job_names:
                raise DagsterInvalidDefinitionError(
                    f'SensorDefinition "{sensor.name}" targets job "{sensor.job_name}" '
                    "which was not found in this repository."
                )

        return sensor
