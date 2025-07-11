import warnings
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, Annotated, Any, Callable, NamedTuple, Optional, Union

from dagster_shared.record import ImportFrom
from dagster_shared.utils.cached_method import get_cached_method_cache
from typing_extensions import Self, TypeAlias

import dagster._check as check
from dagster._annotations import deprecated, preview, public
from dagster._core.definitions import AssetSelection
from dagster._core.definitions.asset_checks.asset_checks_definition import AssetChecksDefinition
from dagster._core.definitions.asset_key import AssetCheckKey
from dagster._core.definitions.asset_selection import CoercibleToAssetSelection
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec, map_asset_specs
from dagster._core.definitions.assets.definition.assets_definition import (
    AssetsDefinition,
    SourceAsset,
)
from dagster._core.definitions.assets.definition.cacheable_assets_definition import (
    CacheableAssetsDefinition,
)
from dagster._core.definitions.assets.graph.asset_graph import AssetGraph
from dagster._core.definitions.decorators import repository
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.executor_definition import ExecutorDefinition
from dagster._core.definitions.job_definition import JobDefinition, default_job_io_manager
from dagster._core.definitions.logger_definition import LoggerDefinition
from dagster._core.definitions.metadata import RawMetadataMapping, normalize_metadata
from dagster._core.definitions.metadata.metadata_value import (
    CodeLocationReconstructionMetadataValue,
    MetadataValue,
)
from dagster._core.definitions.partitions.partitioned_schedule import (
    UnresolvedPartitionedAssetScheduleDefinition,
)
from dagster._core.definitions.repository_definition import (
    SINGLETON_REPOSITORY_NAME,
    RepositoryDefinition,
)
from dagster._core.definitions.schedule_definition import ScheduleDefinition
from dagster._core.definitions.sensor_definition import SensorDefinition
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition
from dagster._core.definitions.utils import dedupe_object_refs
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.execution.build_resources import wrap_resources_for_execution
from dagster._core.execution.with_resources import with_resources
from dagster._core.executor.base import Executor
from dagster._core.instance import DagsterInstance
from dagster._record import IHaveNew, copy, record_custom, replace
from dagster._utils.cached_method import cached_method
from dagster._utils.warnings import disable_dagster_warnings

if TYPE_CHECKING:
    from dagster._core.storage.asset_value_loader import AssetValueLoader
    from dagster.components.core.tree import ComponentTree


TAssets: TypeAlias = Optional[
    Iterable[Union[AssetsDefinition, AssetSpec, SourceAsset, CacheableAssetsDefinition]]
]
TSchedules: TypeAlias = Optional[
    Iterable[Union[ScheduleDefinition, UnresolvedPartitionedAssetScheduleDefinition]]
]
TSensors: TypeAlias = Optional[Iterable[SensorDefinition]]
TJobs: TypeAlias = Optional[Iterable[Union[JobDefinition, UnresolvedAssetJobDefinition]]]
TAssetChecks: TypeAlias = Optional[Iterable[AssetsDefinition]]


@public
def create_repository_using_definitions_args(
    name: str,
    assets: TAssets = None,
    schedules: TSchedules = None,
    sensors: TSensors = None,
    jobs: TJobs = None,
    resources: Optional[Mapping[str, Any]] = None,
    executor: Optional[Union[ExecutorDefinition, Executor]] = None,
    loggers: Optional[Mapping[str, LoggerDefinition]] = None,
    asset_checks: TAssetChecks = None,
) -> RepositoryDefinition:
    """Create a named repository using the same arguments as :py:class:`Definitions`. In older
    versions of Dagster, repositories were the mechanism for organizing assets, schedules, sensors,
    and jobs. There could be many repositories per code location. This was a complicated ontology but
    gave users a way to organize code locations that contained large numbers of heterogenous definitions.

    As a stopgap for those who both want to 1) use the new :py:class:`Definitions` API and 2) but still
    want multiple logical groups of assets in the same code location, we have introduced this function.

    Example usage:

    .. code-block:: python

        named_repo = create_repository_using_definitions_args(
            name="a_repo",
            assets=[asset_one, asset_two],
            schedules=[a_schedule],
            sensors=[a_sensor],
            jobs=[a_job],
            resources={
                "a_resource": some_resource,
            }
        )

    """
    return _create_repository_using_definitions_args(
        name=name,
        assets=assets,
        schedules=schedules,
        sensors=sensors,
        jobs=jobs,
        resources=resources,
        executor=executor,
        loggers=loggers,
        asset_checks=asset_checks,
    )


class _AttachedObjects(NamedTuple):
    jobs: Iterable[Union[JobDefinition, UnresolvedAssetJobDefinition]]
    schedules: Iterable[Union[ScheduleDefinition, UnresolvedPartitionedAssetScheduleDefinition]]
    sensors: Iterable[SensorDefinition]


def _io_manager_needs_replacement(job: JobDefinition, resource_defs: Mapping[str, Any]) -> bool:
    """Explicitly replace the default IO manager in jobs that don't specify one, if a top-level
    I/O manager is provided to Definitions.
    """
    return (
        job.resource_defs.get("io_manager") == default_job_io_manager
        and "io_manager" in resource_defs
    )


def _attach_resources_to_jobs_and_instigator_jobs(
    jobs: Optional[Iterable[Union[JobDefinition, UnresolvedAssetJobDefinition]]],
    schedules: Optional[
        Iterable[Union[ScheduleDefinition, UnresolvedPartitionedAssetScheduleDefinition]]
    ],
    sensors: Optional[Iterable[SensorDefinition]],
    resource_defs: Mapping[str, Any],
) -> _AttachedObjects:
    """Given a list of jobs, schedules, and sensors along with top-level resource definitions,
    attach the resource definitions to the jobs, schedules, and sensors which require them.
    """
    jobs = jobs or []
    schedules = schedules or []
    sensors = sensors or []

    # Add jobs in schedules and sensors as well
    jobs = [
        *jobs,
        *[
            schedule.job
            for schedule in schedules
            if isinstance(schedule, ScheduleDefinition)
            and schedule.target.has_job_def
            and isinstance(schedule.job, (JobDefinition, UnresolvedAssetJobDefinition))
        ],
        *[
            target.job_def
            for sensor in sensors
            for target in sensor.targets
            if target.has_job_def
            and isinstance(target.job_def, (JobDefinition, UnresolvedAssetJobDefinition))
        ],
    ]
    # Dedupe
    jobs = list({id(job): job for job in jobs}.values())

    # Find unsatisfied jobs
    unsatisfied_jobs = [
        job
        for job in jobs
        if isinstance(job, JobDefinition)
        and (
            job.is_missing_required_resources() or _io_manager_needs_replacement(job, resource_defs)
        )
    ]

    # Create a mapping of job id to a version of the job with the resource defs bound
    unsatisfied_job_to_resource_bound_job = {
        id(job): job.with_top_level_resources(
            {
                **resource_defs,
                **job.resource_defs,
                # special case for IO manager - the job-level IO manager does not take precedence
                # if it is the default and a top-level IO manager is provided
                **(
                    {"io_manager": resource_defs["io_manager"]}
                    if _io_manager_needs_replacement(job, resource_defs)
                    else {}
                ),
            }
        )
        for job in jobs
        if job in unsatisfied_jobs
    }

    # Update all jobs to use the resource bound version
    jobs_with_resources = [
        unsatisfied_job_to_resource_bound_job[id(job)] if job in unsatisfied_jobs else job
        for job in jobs
    ]

    # Update all schedules and sensors to use the resource bound version
    updated_schedules = [
        (
            schedule.with_updated_job(unsatisfied_job_to_resource_bound_job[id(schedule.job)])
            if (
                isinstance(schedule, ScheduleDefinition)
                and schedule.target.has_job_def
                and schedule.job in unsatisfied_jobs
            )
            else schedule
        )
        for schedule in schedules
    ]
    updated_sensors = [
        (
            sensor.with_updated_jobs(
                [
                    (
                        unsatisfied_job_to_resource_bound_job[id(job)]
                        if job in unsatisfied_jobs
                        else job
                    )
                    for job in sensor.jobs
                ]
            )
            if any(target.has_job_def for target in sensor.targets)
            and any(job in unsatisfied_jobs for job in sensor.jobs)
            else sensor
        )
        for sensor in sensors
    ]

    return _AttachedObjects(jobs_with_resources, updated_schedules, updated_sensors)


def _create_repository_using_definitions_args(
    name: str,
    assets: TAssets = None,
    schedules: TSchedules = None,
    sensors: TSensors = None,
    jobs: TJobs = None,
    resources: Optional[Mapping[str, Any]] = None,
    executor: Optional[Union[ExecutorDefinition, Executor]] = None,
    loggers: Optional[Mapping[str, LoggerDefinition]] = None,
    asset_checks: TAssetChecks = None,
    metadata: Optional[RawMetadataMapping] = None,
    component_tree: Optional["ComponentTree"] = None,
) -> RepositoryDefinition:
    # First, dedupe all definition types.
    sensors = dedupe_object_refs(sensors)
    jobs = dedupe_object_refs(jobs)
    assets = _canonicalize_specs_to_assets_defs(dedupe_object_refs(assets))
    schedules = dedupe_object_refs(schedules)
    asset_checks = dedupe_object_refs(asset_checks)

    executor_def = (
        executor
        if isinstance(executor, ExecutorDefinition) or executor is None
        else ExecutorDefinition.hardcoded_executor(executor)
    )

    resource_defs = wrap_resources_for_execution(resources)

    # Binds top-level resources to jobs and any jobs attached to schedules or sensors
    (
        jobs_with_resources,
        schedules_with_resources,
        sensors_with_resources,
    ) = _attach_resources_to_jobs_and_instigator_jobs(jobs, schedules, sensors, resource_defs)

    @repository(
        name=name,
        default_executor_def=executor_def,
        default_logger_defs=loggers,
        metadata=metadata,
        _top_level_resources=resource_defs,
        _component_tree=component_tree,
    )
    def created_repo():
        return [
            *with_resources(assets, resource_defs),
            *with_resources(asset_checks or [], resource_defs),
            *(schedules_with_resources),
            *(sensors_with_resources),
            *(jobs_with_resources),
        ]

    return created_repo


def _canonicalize_specs_to_assets_defs(
    assets: Iterable[Union[AssetsDefinition, AssetSpec, SourceAsset, CacheableAssetsDefinition]],
) -> Iterable[Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition]]:
    asset_specs_by_partitions_def = defaultdict(list)
    for obj in assets:
        if isinstance(obj, AssetSpec):
            asset_specs_by_partitions_def[obj.partitions_def].append(obj)
    result = [obj for obj in assets if not isinstance(obj, AssetSpec)]

    for specs in asset_specs_by_partitions_def.values():
        with disable_dagster_warnings():
            result.append(AssetsDefinition(specs=specs))

    return result


@deprecated(
    breaking_version="2.0",
    additional_warn_text=(
        "Instantiations can be removed. Since it's behavior is now the default, this class is now a"
        " no-op."
    ),
)
class BindResourcesToJobs(list):
    """Used to instruct Dagster to bind top-level resources to jobs and any jobs attached to schedules
    and sensors. Now deprecated since this behavior is the default.
    """


@record_custom
class Definitions(IHaveNew):
    """A set of definitions explicitly available and loadable by Dagster tools.

    Parameters:
        assets (Optional[Iterable[Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition]]]):
            A list of assets. Assets can be created by annotating
            a function with :py:func:`@asset <asset>` or
            :py:func:`@observable_source_asset <observable_source_asset>`.
            Or they can by directly instantiating :py:class:`AssetsDefinition`,
            :py:class:`SourceAsset`, or :py:class:`CacheableAssetsDefinition`.

        asset_checks (Optional[Iterable[AssetChecksDefinition]]):
            A list of asset checks.

        schedules (Optional[Iterable[Union[ScheduleDefinition, UnresolvedPartitionedAssetScheduleDefinition]]]):
            List of schedules.

        sensors (Optional[Iterable[SensorDefinition]]):
            List of sensors, typically created with :py:func:`@sensor <sensor>`.

        jobs (Optional[Iterable[Union[JobDefinition, UnresolvedAssetJobDefinition]]]):
            List of jobs. Typically created with :py:func:`define_asset_job <define_asset_job>`
            or with :py:func:`@job <job>` for jobs defined in terms of ops directly.
            Jobs created with :py:func:`@job <job>` must already have resources bound
            at job creation time. They do not respect the `resources` argument here.

        resources (Optional[Mapping[str, Any]]): Dictionary of resources to bind to assets.
            The resources dictionary takes raw Python objects,
            not just instances of :py:class:`ResourceDefinition`. If that raw object inherits from
            :py:class:`IOManager`, it gets coerced to an :py:class:`IOManagerDefinition`.
            Any other object is coerced to a :py:class:`ResourceDefinition`.
            These resources will be automatically bound
            to any assets passed to this Definitions instance using
            :py:func:`with_resources <with_resources>`. Assets passed to Definitions with
            resources already bound using :py:func:`with_resources <with_resources>` will
            override this dictionary.

        executor (Optional[Union[ExecutorDefinition, Executor]]):
            Default executor for jobs. Individual jobs can override this and define their own executors
            by setting the executor on :py:func:`@job <job>` or :py:func:`define_asset_job <define_asset_job>`
            explicitly. This executor will also be used for materializing assets directly
            outside of the context of jobs. If an :py:class:`Executor` is passed, it is coerced into
            an :py:class:`ExecutorDefinition`.

        loggers (Optional[Mapping[str, LoggerDefinition]):
            Default loggers for jobs. Individual jobs
            can define their own loggers by setting them explictly.

        metadata (Optional[MetadataMapping]):
            Arbitrary metadata for the Definitions. Not displayed in the UI but accessible on
            the Definitions instance at runtime.

        component_tree (Optional[ComponentTree]):
            Information about the Components that were used to construct part of this
            Definitions object.


    Example usage:

    .. code-block:: python

        Definitions(
            assets=[asset_one, asset_two],
            schedules=[a_schedule],
            sensors=[a_sensor],
            jobs=[a_job],
            resources={
                "a_resource": some_resource,
            },
            asset_checks=[asset_one_check_one]
        )

    Dagster separates user-defined code from system tools such the web server and
    the daemon. Rather than loading code directly into process, a tool such as the
    webserver interacts with user-defined code over a serialization boundary.

    These tools must be able to locate and load this code when they start. Via CLI
    arguments or config, they specify a Python module to inspect.

    A Python module is loadable by Dagster tools if there is a top-level variable
    that is an instance of :py:class:`Definitions`.
    """

    assets: TAssets = None
    schedules: TSchedules = None
    sensors: TSensors = None
    jobs: TJobs = None
    resources: Optional[Mapping[str, Any]] = None
    executor: Optional[Union[ExecutorDefinition, Executor]] = None
    loggers: Optional[Mapping[str, LoggerDefinition]] = None
    # There's a bug that means that sometimes it's Dagster's fault when AssetsDefinitions are
    # passed here instead of AssetChecksDefinitions: https://github.com/dagster-io/dagster/issues/22064.
    # After we fix the bug, we should remove AssetsDefinition from the set of accepted types.
    asset_checks: TAssetChecks = None
    metadata: Mapping[str, MetadataValue]
    component_tree: Optional[Annotated["ComponentTree", ImportFrom("dagster.components.core.tree")]]

    def __new__(
        cls,
        assets: TAssets = None,
        schedules: TSchedules = None,
        sensors: TSensors = None,
        jobs: TJobs = None,
        resources: Optional[Mapping[str, Any]] = None,
        executor: Optional[Union[ExecutorDefinition, Executor]] = None,
        loggers: Optional[Mapping[str, LoggerDefinition]] = None,
        asset_checks: TAssetChecks = None,
        metadata: Optional[RawMetadataMapping] = None,
        component_tree: Optional["ComponentTree"] = None,
    ):
        instance = super().__new__(
            cls,
            assets=assets,
            schedules=schedules,
            sensors=sensors,
            jobs=jobs,
            resources=resources,
            executor=executor,
            loggers=loggers,
            asset_checks=asset_checks,
            metadata=normalize_metadata(check.opt_mapping_param(metadata, "metadata")),
            component_tree=component_tree,
        )

        check.invariant(
            not instance.has_resolved_repository_def(),
            "Definitions object should not have been resolved",
        )

        return instance

    @public
    def get_job_def(self, name: str) -> JobDefinition:
        """Get a job definition by name. This will only return a `JobDefinition` if it was directly passed in to the `Definitions` object.

        If that is not found, the Definitions object is resolved (transforming UnresolvedAssetJobDefinitions to JobDefinitions and an example). It
        also finds jobs passed to sensors and schedules and retrieves them from the repository.

        After dagster 1.11, this resolution step will not happen, and will throw an error if the job is not found.
        """
        found_direct = False
        for job in self.jobs or []:
            if job.name == name:
                if isinstance(job, JobDefinition):
                    found_direct = True

        if not found_direct:
            warning = self.dig_for_warning(name)
            if warning:
                warnings.warn(warning)
            else:
                warnings.warn(
                    f"JobDefinition with name {name} directly passed to Definitions not found, "
                    "will attempt to resolve to a JobDefinition. "
                    "This will be an error in a future release and will require a call to "
                    "resolve_job_def in dagster 1.11. "
                )

        return self.resolve_job_def(name)

    def resolve_job_def(self, name: str) -> JobDefinition:
        """Resolve a job definition by name. If you passed in an :py:class:`UnresolvedAssetJobDefinition`
        (return value of :py:func:`define_asset_job`) it will be resolved to a :py:class:`JobDefinition` when returned
        from this function, with all resource dependencies fully resolved.
        """
        check.str_param(name, "name")
        return self.get_repository_def().get_job(name)

    def dig_for_warning(self, name: str) -> Optional[str]:
        for job in self.jobs or []:
            if job.name == name:
                if isinstance(job, JobDefinition):
                    return None
                return (
                    f"Found asset job named {job.name} of type {type(job)} passed to `jobs` parameter. Starting in "
                    "dagster 1.11, you must now use Definitions.resolve_job_def to correctly "
                    "retrieve this job definition."
                )

        for sensor in self.sensors or []:
            for job in sensor.jobs:
                if job.name == name:
                    return (
                        f"Found job or graph named {job.name} passed to sensor named {sensor.name} "
                        "that was passed to Definitions in the sensors param. Starting in dagster 1.11, "
                        "you must call Definitions.resolve_job_def to retrieve this job definition."
                    )

        for schedule in self.schedules or []:
            job = schedule.job
            if job.name == name:
                return (
                    f"Found job named {job.name} passed to schedule named {schedule.name} "
                    "that was passed to Definitions in the schedules param. Starting in dagster 1.11, "
                    "you must call Definitions.resolve_job_def to retrieve this job definition."
                )
        return None

    @public
    def get_sensor_def(self, name: str) -> SensorDefinition:
        """Get a :py:class:`SensorDefinition` by name.
        If your passed-in sensor had resource dependencies, or the job targeted by the sensor had
        resource dependencies, those resource dependencies will be fully resolved on the returned object.
        """
        warnings.warn(
            "Starting in dagster 1.11, get_sensor_def will return a SensorDefinition without resolving resource dependencies on it or its target."
        )

        return self.resolve_sensor_def(name)

    # TODO: after dagster 1.11, this will become the implementation of get_sensor_def -- schrockn 2025-06-02
    def get_unresolved_sensor_def(self, name: str) -> SensorDefinition:
        for sensor in self.sensors or []:
            if sensor.name == name:
                return sensor
        raise ValueError(f"SensorDefinition with name {name} not found")

    def resolve_sensor_def(self, name: str) -> SensorDefinition:
        check.str_param(name, "name")
        return self.get_repository_def().get_sensor_def(name)

    @public
    def get_schedule_def(self, name: str) -> ScheduleDefinition:
        """Get a :py:class:`ScheduleDefinition` by name.
        If your passed-in schedule had resource dependencies, or the job targeted by the schedule had
        resource dependencies, those resource dependencies will be fully resolved on the returned object.
        """
        warnings.warn(
            "Starting in dagster 1.11, get_schedule_def will return a ScheduleDefinition without resolving resource dependencies on it or its target."
        )
        return self.resolve_schedule_def(name)

    # TODO: after dagster 1.11, this will become the implementation of get_schedule_def -- schrockn 2025-06-02
    def get_unresolved_schedule_def(self, name: str) -> ScheduleDefinition:
        for schedule in self.schedules or []:
            if schedule.name == name:
                if isinstance(schedule, ScheduleDefinition):
                    return schedule
                raise ValueError(
                    f"ScheduleDefinition with name {name} is an UnresolvedPartitionedAssetScheduleDefinition, which is not supported in get_unresolved_schedule_def"
                )

        raise ValueError(f"ScheduleDefinition with name {name} not found")

    def resolve_schedule_def(self, name: str) -> ScheduleDefinition:
        check.str_param(name, "name")
        return self.get_repository_def().get_schedule_def(name)

    @public
    def load_asset_value(
        self,
        asset_key: CoercibleToAssetKey,
        *,
        python_type: Optional[type] = None,
        instance: Optional[DagsterInstance] = None,
        partition_key: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> object:
        """Load the contents of an asset as a Python object.

        Invokes `load_input` on the :py:class:`IOManager` associated with the asset.

        If you want to load the values of multiple assets, it's more efficient to use
        :py:meth:`~dagster.Definitions.get_asset_value_loader`, which avoids spinning up
        resources separately for each asset.

        Args:
            asset_key (Union[AssetKey, Sequence[str], str]): The key of the asset to load.
            python_type (Optional[Type]): The python type to load the asset as. This is what will
                be returned inside `load_input` by `context.dagster_type.typing_type`.
            partition_key (Optional[str]): The partition of the asset to load.
            metadata (Optional[Dict[str, Any]]): Input metadata to pass to the :py:class:`IOManager`
                (is equivalent to setting the metadata argument in `In` or `AssetIn`).

        Returns:
            The contents of an asset as a Python object.
        """
        return self.get_repository_def().load_asset_value(
            asset_key=asset_key,
            python_type=python_type,
            instance=instance,
            partition_key=partition_key,
            metadata=metadata,
        )

    @public
    def get_asset_value_loader(
        self, instance: Optional[DagsterInstance] = None
    ) -> "AssetValueLoader":
        """Returns an object that can load the contents of assets as Python objects.

        Invokes `load_input` on the :py:class:`IOManager` associated with the assets. Avoids
        spinning up resources separately for each asset.

        Usage:

        .. code-block:: python

            with defs.get_asset_value_loader() as loader:
                asset1 = loader.load_asset_value("asset1")
                asset2 = loader.load_asset_value("asset2")
        """
        return self.get_repository_def().get_asset_value_loader(
            instance=instance,
        )

    def resolve_all_job_defs(self) -> Sequence[JobDefinition]:
        """Get all the Job definitions in the project.
        This includes both jobs passed into the Definitions object and any implicit jobs created.
        All jobs returned from this function will have all resource dependencies resolved.
        """
        return self.get_repository_def().get_all_jobs()

    def has_implicit_global_asset_job_def(self) -> bool:
        return self.get_repository_def().has_implicit_global_asset_job_def()

    def get_implicit_global_asset_job_def(self) -> JobDefinition:
        warnings.warn(
            "This will be renamed to resolve_implicit_global_asset_job_def in dagster 1.11"
        )
        return self.get_repository_def().get_implicit_global_asset_job_def()

    def resolve_implicit_global_asset_job_def(self) -> JobDefinition:
        """A useful conveninence method when there is a single defined global asset job.
        This occurs when all assets in the project use a single partitioning scheme.
        If there are multiple partitioning schemes you must use get_implicit_job_def_for_assets
        instead to access to the correct implicit asset one.
        """
        return self.get_repository_def().get_implicit_global_asset_job_def()

    def resolve_implicit_job_def_def_for_assets(
        self, asset_keys: Iterable[AssetKey]
    ) -> Optional[JobDefinition]:
        return self.get_repository_def().get_implicit_job_def_for_assets(asset_keys)

    def get_assets_def(self, key: CoercibleToAssetKey) -> AssetsDefinition:
        key = AssetKey.from_coercible(key)
        # Sadly both self.assets and self.asset_checks can contain either AssetsDefinition or AssetChecksDefinition
        # objects. We need to check both collections and exclude the AssetChecksDefinition objects.
        for asset in [*(self.assets or []), *(self.asset_checks or [])]:
            if isinstance(asset, AssetsDefinition) and not isinstance(asset, AssetChecksDefinition):
                if key in asset.keys:
                    return asset

        warnings.warn(
            f"Could not find assets_def with key {key} directly passed to Definitions. This will be an error starting in 1.11 and will require a call to resolve_assets_def in dagster 1.11."
        )

        return self.resolve_assets_def(key)

    def get_asset_checks_def(self, key: AssetCheckKey) -> AssetChecksDefinition:
        for possible_assets_check_def in [*(self.assets or []), *(self.asset_checks or [])]:
            if (
                isinstance(possible_assets_check_def, AssetChecksDefinition)
                and key in possible_assets_check_def.asset_and_check_keys
            ):
                return possible_assets_check_def

        raise DagsterInvariantViolationError(f"Could not find asset checks defs for {key}")

    def resolve_assets_def(self, key: CoercibleToAssetKey) -> AssetsDefinition:
        asset_key = AssetKey.from_coercible(key)
        for assets_def in self.resolve_asset_graph().assets_defs:
            if asset_key in assets_def.keys:
                return assets_def

        raise DagsterInvariantViolationError(f"Could not find asset {asset_key}")

    @cached_method
    def get_repository_def(self) -> RepositoryDefinition:
        """Definitions is implemented by wrapping RepositoryDefinition. Get that underlying object
        in order to access any functionality which is not exposed on Definitions.
        """
        return _create_repository_using_definitions_args(
            name=SINGLETON_REPOSITORY_NAME,
            assets=self.assets,
            schedules=self.schedules,
            sensors=self.sensors,
            jobs=self.jobs,
            resources=self.resources,
            executor=self.executor,
            loggers=self.loggers,
            asset_checks=self.asset_checks,
            metadata=self.metadata,
            component_tree=self.component_tree,
        )

    def resolve_asset_graph(self) -> AssetGraph:
        """Get the AssetGraph for this set of definitions."""
        return self.get_repository_def().asset_graph

    @public
    @staticmethod
    def validate_loadable(defs: "Definitions") -> None:
        """Validates that the enclosed definitions will be loadable by Dagster:
        - No assets have conflicting keys.
        - No jobs, sensors, or schedules have conflicting names.
        - All asset jobs can be resolved.
        - All resource requirements are satisfied.
        - All partition mappings are valid.

        Meant to be used in unit tests.

        Raises an error if any of the above are not true.
        """
        defs.get_repository_def().validate_loadable()

    @public
    @staticmethod
    def merge(*def_sets: "Definitions") -> "Definitions":
        """Merges multiple Definitions objects into a single Definitions object.

        The returned Definitions object has the union of all the definitions in the input
        Definitions objects.

        Raises an error if the Definitions objects to be merged contain conflicting values for the
        same resource key or logger key, or if they have different executors defined.

        Examples:
            .. code-block:: python

                import submodule1
                import submodule2

                defs = Definitions.merge(submodule1.defs, submodule2.defs)

        Returns:
            Definitions: The merged definitions.
        """
        check.sequence_param(def_sets, "def_sets", of_type=Definitions)
        assets = []
        schedules = []
        sensors = []
        jobs = []
        asset_checks = []
        metadata = {}
        component_tree = None

        resources = {}
        resource_key_indexes: dict[str, int] = {}
        loggers = {}
        logger_key_indexes: dict[str, int] = {}
        executor = None
        executor_index: Optional[int] = None

        for i, def_set in enumerate(def_sets):
            assets.extend(def_set.assets or [])
            asset_checks.extend(def_set.asset_checks or [])
            schedules.extend(def_set.schedules or [])
            sensors.extend(def_set.sensors or [])
            jobs.extend(def_set.jobs or [])
            metadata.update(def_set.metadata)

            for resource_key, resource_value in (def_set.resources or {}).items():
                if resource_key in resources and resources[resource_key] is not resource_value:
                    raise DagsterInvariantViolationError(
                        f"Definitions objects {resource_key_indexes[resource_key]} and {i} have "
                        f"different resources with same key '{resource_key}'"
                    )
                resources[resource_key] = resource_value
                resource_key_indexes[resource_key] = i

            for logger_key, logger_value in (def_set.loggers or {}).items():
                if logger_key in loggers and loggers[logger_key] is not logger_value:
                    raise DagsterInvariantViolationError(
                        f"Definitions objects {logger_key_indexes[logger_key]} and {i} have "
                        f"different loggers with same key '{logger_key}'"
                    )
                loggers[logger_key] = logger_value
                logger_key_indexes[logger_key] = i

            if def_set.executor is not None:
                if executor is not None and executor is not def_set.executor:
                    raise DagsterInvariantViolationError(
                        f"Definitions objects {executor_index} and {i} both have an executor"
                    )

                executor = def_set.executor
                executor_index = i

            if def_set.component_tree:
                if component_tree is not None:
                    raise DagsterInvariantViolationError(
                        "Can not merge Definitions that both contain component_tree."
                    )

                component_tree = def_set.component_tree

            # This check is commented out now, since it's possible that particular component
            # Definitions are resolved by another component
            # check.invariant(
            #     not def_set.has_resolved_repository_def(),
            #     "Definitions object should have been resolved",
            # )
        return Definitions(
            assets=assets,
            schedules=schedules,
            sensors=sensors,
            jobs=jobs,
            resources=resources,
            executor=executor,
            loggers=loggers,
            asset_checks=asset_checks,
            metadata=metadata,
            component_tree=component_tree,
        )

    @public
    @deprecated(
        breaking_version="1.11",
        additional_warn_text="Use resolve_all_asset_specs instead",
        subject="get_all_asset_specs",
    )
    def get_all_asset_specs(self) -> Sequence[AssetSpec]:
        """Returns an AssetSpec object for AssetsDefinitions and AssetSpec passed directly to the Definitions object."""
        return self.resolve_all_asset_specs()

    @public
    def resolve_all_asset_specs(self) -> Sequence[AssetSpec]:
        """Returns an AssetSpec object for every asset contained inside the resolved Definitions object."""
        asset_graph = self.resolve_asset_graph()
        return [asset_node.to_asset_spec() for asset_node in asset_graph.asset_nodes]

    @public
    def resolve_all_asset_keys(self) -> Sequence[AssetKey]:
        """Returns an AssetKey object for every asset contained inside the resolved Definitions object."""
        return [spec.key for spec in self.resolve_all_asset_specs()]

    @preview
    def with_reconstruction_metadata(self, reconstruction_metadata: Mapping[str, str]) -> Self:
        """Add reconstruction metadata to the Definitions object. This is typically used to cache data
        loaded from some external API that is computed during initialization of a code server.
        The cached data is then made available on the DefinitionsLoadContext during
        reconstruction of the same project context (such as a run worker), allowing use of the
        cached data to avoid additional external API queries. Values are expected to be serialized
        in advance and must be strings.
        """
        check.mapping_param(reconstruction_metadata, "reconstruction_metadata", key_type=str)
        for k, v in reconstruction_metadata.items():
            if not isinstance(v, str):
                raise DagsterInvariantViolationError(
                    f"Reconstruction metadata values must be strings. State-representing values are"
                    f" expected to be serialized before being passed as reconstruction metadata."
                    f" Got for key {k}:\n\n{v}"
                )
        normalized_metadata = {
            k: CodeLocationReconstructionMetadataValue(v)
            for k, v in reconstruction_metadata.items()
        }
        return copy(
            self,
            metadata={
                **(self.metadata or {}),
                **normalized_metadata,
            },
        )

    @public
    @preview
    def map_asset_specs(
        self,
        *,
        func: Callable[[AssetSpec], AssetSpec],
        selection: Optional[CoercibleToAssetSelection] = None,
    ) -> "Definitions":
        """Map a function over the included AssetSpecs or AssetsDefinitions in this Definitions object, replacing specs in the sequence
        or specs in an AssetsDefinitions with the result of the function.

        Args:
            func (Callable[[AssetSpec], AssetSpec]): The function to apply to each AssetSpec.
            selection (Optional[Union[str, Sequence[str], Sequence[AssetKey], Sequence[Union[AssetsDefinition, SourceAsset]], AssetSelection]]): An asset selection to narrow down the set of assets to apply the function to. If not provided, applies to all assets.

        Returns:
            Definitions: A Definitions object where the AssetSpecs have been replaced with the result of the function where the selection applies.

        Examples:
            .. code-block:: python

                import dagster as dg

                my_spec = dg.AssetSpec("asset1")

                @dg.asset
                def asset1(_): ...

                @dg.asset
                def asset2(_): ...

                defs = Definitions(
                    assets=[asset1, asset2]
                )

                # Applies to asset1 and asset2
                mapped_defs = defs.map_asset_specs(
                    func=lambda s: s.merge_attributes(metadata={"new_key": "new_value"}),
                )

        """
        check.invariant(
            selection is None,
            "The selection parameter is no longer supported for map_asset_specs, Please use map_resolved_asset_specs instead",
        )

        return self.map_resolved_asset_specs(func=func, selection=None)

    @public
    @preview
    def map_resolved_asset_specs(
        self,
        *,
        func: Callable[[AssetSpec], AssetSpec],
        selection: Optional[CoercibleToAssetSelection] = None,
    ) -> "Definitions":
        """Map a function over the included AssetSpecs or AssetsDefinitions in this Definitions object, replacing specs in the sequence.

        See map_asset_specs for more details.

        Supports selection and therefore requires resolving the Definitions object to a RepositoryDefinition when there is a selection.

        Examples:
            .. code-block:: python

                import dagster as dg

                my_spec = dg.AssetSpec("asset1")

                @dg.asset
                def asset1(_): ...

                @dg.asset
                def asset2(_): ...

                # Applies only to asset1
                mapped_defs = defs.map_resolved_asset_specs(
                    func=lambda s: s.replace_attributes(metadata={"new_key": "new_value"}),
                    selection="asset1",
                )
        """
        non_spec_asset_types = {
            type(d) for d in self.assets or [] if not isinstance(d, (AssetsDefinition, AssetSpec))
        }

        if non_spec_asset_types:
            raise DagsterInvariantViolationError(
                "Can only map over AssetSpec or AssetsDefinition objects. "
                "Received objects of types: "
                f"{non_spec_asset_types}."
            )

        return self.permissive_map_resolved_asset_specs(
            func=func,
            selection=selection,
        )

    def permissive_map_resolved_asset_specs(
        self,
        func: Callable[[AssetSpec], AssetSpec],
        selection: Optional[CoercibleToAssetSelection],
    ) -> "Definitions":
        """This is a permissive version of map_resolved_asset_specs that allows for non-spec asset types, i.e. SourceAssets and CacheableAssetsDefinitions."""
        target_keys = None
        if selection:
            if isinstance(selection, str):
                selection = AssetSelection.from_string(selection, include_sources=True)
            else:
                selection = AssetSelection.from_coercible(selection)
            target_keys = selection.resolve(self.resolve_asset_graph())
        mappable = iter(
            d for d in self.assets or [] if isinstance(d, (AssetsDefinition, AssetSpec))
        )
        mapped_assets = map_asset_specs(
            lambda spec: func(spec) if (target_keys is None or spec.key in target_keys) else spec,
            mappable,
        )

        assets = [
            *mapped_assets,
            *[d for d in self.assets or [] if not isinstance(d, (AssetsDefinition, AssetSpec))],
        ]
        return replace(self, assets=assets)

    def with_resources(self, resources: Optional[Mapping[str, Any]]) -> "Definitions":
        return Definitions.merge(self, Definitions(resources=resources)) if resources else self

    def has_resolved_repository_def(self) -> bool:
        return len(get_cached_method_cache(self, self.get_repository_def.__name__)) > 0

    def with_definition_metadata_update(
        self, update: Callable[[RawMetadataMapping], RawMetadataMapping]
    ):
        """Run a provided update function on every contained definition that supports it
        to updated its metadata. Return a new Definitions object containing the updated objects.
        """
        return replace(
            self,
            jobs=_update_jobs_metadata(self.jobs, update),
            schedules=_update_schedules_metadata(self.schedules, update),
            sensors=_update_sensors_metadata(self.sensors, update),
            assets=_update_assets_metadata(self.assets, update),
            asset_checks=_update_checks_metadata(self.asset_checks, update),
        )


def _update_assets_metadata(
    assets: TAssets,
    update: Callable[[RawMetadataMapping], RawMetadataMapping],
) -> TAssets:
    if not assets:
        return assets

    updated_assets = []
    for asset in assets:
        if isinstance(asset, AssetsDefinition):
            updated_assets.append(_update_assets_def_metadata(asset, update))
        elif isinstance(asset, AssetSpec):
            updated_assets.append(asset.replace_attributes(metadata=update(asset.metadata)))
        elif isinstance(asset, (SourceAsset, CacheableAssetsDefinition)):
            # these types are deprecated and do not support metadata updates, ignore
            updated_assets.append(asset)
        else:
            check.assert_never(asset)
    return updated_assets


def _update_schedules_metadata(
    schedules: TSchedules,
    update: Callable[[RawMetadataMapping], RawMetadataMapping],
) -> TSchedules:
    if not schedules:
        return schedules

    updated_schedules = []
    for schedule in schedules:
        if isinstance(schedule, ScheduleDefinition):
            updated_schedules.append(schedule.with_attributes(metadata=update(schedule.metadata)))
        elif isinstance(schedule, UnresolvedPartitionedAssetScheduleDefinition):
            updated_schedules.append(schedule.with_metadata(update(schedule.metadata or {})))
        else:
            check.assert_never(schedule)

    return updated_schedules


def _update_sensors_metadata(
    sensors: TSensors,
    update: Callable[[RawMetadataMapping], RawMetadataMapping],
) -> TSensors:
    if not sensors:
        return sensors

    updated_sensors = []
    for sensor in sensors:
        if isinstance(sensor, SensorDefinition):
            updated_sensors.append(sensor.with_attributes(metadata=update(sensor.metadata)))
        else:
            check.assert_never(sensor)

    return updated_sensors


def _update_jobs_metadata(
    jobs: TJobs,
    update: Callable[[RawMetadataMapping], RawMetadataMapping],
) -> TJobs:
    if not jobs:
        return jobs

    updated_jobs = []
    for job in jobs:
        if isinstance(job, JobDefinition):
            updated_jobs.append(job.with_metadata(update(job.metadata)))
        elif isinstance(job, UnresolvedAssetJobDefinition):
            updated_jobs.append(job.with_metadata(update(job.metadata or {})))
        else:
            check.assert_never(job)

    return updated_jobs


def _update_checks_metadata(
    asset_checks: TAssetChecks,
    update: Callable[[RawMetadataMapping], RawMetadataMapping],
) -> TAssetChecks:
    if not asset_checks:
        return asset_checks

    updated_checks = []
    for asset_check in asset_checks:
        if isinstance(asset_check, AssetsDefinition):
            updated_checks.append(_update_assets_def_metadata(asset_check, update))
        else:
            check.assert_never(asset_check)

    return updated_checks


def _update_assets_def_metadata(
    assets_def: AssetsDefinition,
    update: Callable[[RawMetadataMapping], RawMetadataMapping],
) -> AssetsDefinition:
    return assets_def.with_attributes(
        metadata_by_key={
            **{key: update(metadata) for key, metadata in assets_def.metadata_by_key.items()},
            **{c.key: update(c.metadata) for c in assets_def.check_specs},
        }
    )
