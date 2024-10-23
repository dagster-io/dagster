from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Type,
    Union,
)

from typing_extensions import Self

import dagster._check as check
from dagster._annotations import deprecated, experimental, public
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition, SourceAsset
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition
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
from dagster._core.definitions.partitioned_schedule import (
    UnresolvedPartitionedAssetScheduleDefinition,
)
from dagster._core.definitions.repository_definition import (
    SINGLETON_REPOSITORY_NAME,
    PendingRepositoryDefinition,
    RepositoryDefinition,
)
from dagster._core.definitions.schedule_definition import ScheduleDefinition
from dagster._core.definitions.sensor_definition import SensorDefinition
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition
from dagster._core.definitions.utils import (
    add_default_automation_condition_sensor,
    dedupe_object_refs,
)
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.execution.build_resources import wrap_resources_for_execution
from dagster._core.execution.with_resources import with_resources
from dagster._core.executor.base import Executor
from dagster._core.instance import DagsterInstance
from dagster._record import IHaveNew, copy, record_custom
from dagster._utils.cached_method import cached_method
from dagster._utils.warnings import disable_dagster_warnings

if TYPE_CHECKING:
    from dagster._core.storage.asset_value_loader import AssetValueLoader


@public
@experimental
def create_repository_using_definitions_args(
    name: str,
    assets: Optional[
        Iterable[Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition]]
    ] = None,
    schedules: Optional[
        Iterable[Union[ScheduleDefinition, UnresolvedPartitionedAssetScheduleDefinition]]
    ] = None,
    sensors: Optional[Iterable[SensorDefinition]] = None,
    jobs: Optional[Iterable[Union[JobDefinition, UnresolvedAssetJobDefinition]]] = None,
    resources: Optional[Mapping[str, Any]] = None,
    executor: Optional[Union[ExecutorDefinition, Executor]] = None,
    loggers: Optional[Mapping[str, LoggerDefinition]] = None,
    asset_checks: Optional[Iterable[AssetChecksDefinition]] = None,
) -> Union[RepositoryDefinition, PendingRepositoryDefinition]:
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


def _jobs_which_will_have_io_manager_replaced(
    jobs: Optional[Iterable[Union[JobDefinition, UnresolvedAssetJobDefinition]]],
    resource_defs: Mapping[str, Any],
) -> List[Union[JobDefinition, UnresolvedAssetJobDefinition]]:
    """Returns whether any jobs will have their I/O manager replaced by an `io_manager` override from
    the top-level `resource_defs` provided to `Definitions` in 1.3. We will warn users if this is
    the case.
    """
    jobs = jobs or []
    return [
        job
        for job in jobs
        if isinstance(job, JobDefinition) and _io_manager_needs_replacement(job, resource_defs)
    ]


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
    assets: Optional[
        Iterable[Union[AssetsDefinition, AssetSpec, SourceAsset, CacheableAssetsDefinition]]
    ] = None,
    schedules: Optional[
        Iterable[Union[ScheduleDefinition, UnresolvedPartitionedAssetScheduleDefinition]]
    ] = None,
    sensors: Optional[Iterable[SensorDefinition]] = None,
    jobs: Optional[Iterable[Union[JobDefinition, UnresolvedAssetJobDefinition]]] = None,
    resources: Optional[Mapping[str, Any]] = None,
    executor: Optional[Union[ExecutorDefinition, Executor]] = None,
    loggers: Optional[Mapping[str, LoggerDefinition]] = None,
    asset_checks: Optional[Iterable[AssetsDefinition]] = None,
    metadata: Optional[RawMetadataMapping] = None,
) -> Union[RepositoryDefinition, PendingRepositoryDefinition]:
    # First, dedupe all definition types.
    sensors = dedupe_object_refs(sensors)
    jobs = dedupe_object_refs(jobs)
    assets = _canonicalize_specs_to_assets_defs(dedupe_object_refs(assets))
    schedules = dedupe_object_refs(schedules)
    asset_checks = dedupe_object_refs(asset_checks)

    # add in a default automation condition sensor definition if required
    sensors = add_default_automation_condition_sensor(
        sensors,
        [asset for asset in assets if not isinstance(asset, CacheableAssetsDefinition)],
        asset_checks or [],
    )

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
        _top_level_resources=resource_defs,
        metadata=metadata,
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

    Example usage:

    .. code-block:: python

        defs = Definitions(
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

    assets: Optional[
        Iterable[Union[AssetsDefinition, AssetSpec, SourceAsset, CacheableAssetsDefinition]]
    ] = None
    schedules: Optional[
        Iterable[Union[ScheduleDefinition, UnresolvedPartitionedAssetScheduleDefinition]]
    ] = None
    sensors: Optional[Iterable[SensorDefinition]] = None
    jobs: Optional[Iterable[Union[JobDefinition, UnresolvedAssetJobDefinition]]] = None
    resources: Optional[Mapping[str, Any]] = None
    executor: Optional[Union[ExecutorDefinition, Executor]] = None
    loggers: Optional[Mapping[str, LoggerDefinition]] = None
    # There's a bug that means that sometimes it's Dagster's fault when AssetsDefinitions are
    # passed here instead of AssetChecksDefinitions: https://github.com/dagster-io/dagster/issues/22064.
    # After we fix the bug, we should remove AssetsDefinition from the set of accepted types.
    asset_checks: Optional[Iterable[AssetsDefinition]] = None
    metadata: Mapping[str, MetadataValue]

    def __new__(
        cls,
        assets: Optional[
            Iterable[Union[AssetsDefinition, AssetSpec, SourceAsset, CacheableAssetsDefinition]]
        ] = None,
        schedules: Optional[
            Iterable[Union[ScheduleDefinition, UnresolvedPartitionedAssetScheduleDefinition]]
        ] = None,
        sensors: Optional[Iterable[SensorDefinition]] = None,
        jobs: Optional[Iterable[Union[JobDefinition, UnresolvedAssetJobDefinition]]] = None,
        resources: Optional[Mapping[str, Any]] = None,
        executor: Optional[Union[ExecutorDefinition, Executor]] = None,
        loggers: Optional[Mapping[str, LoggerDefinition]] = None,
        asset_checks: Optional[Iterable[AssetsDefinition]] = None,
        metadata: Optional[RawMetadataMapping] = None,
    ):
        return super().__new__(
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
        )

    @public
    def get_job_def(self, name: str) -> JobDefinition:
        """Get a job definition by name. If you passed in a an :py:class:`UnresolvedAssetJobDefinition`
        (return value of :py:func:`define_asset_job`) it will be resolved to a :py:class:`JobDefinition` when returned
        from this function, with all resource dependencies fully resolved.
        """
        check.str_param(name, "name")
        return self.get_repository_def().get_job(name)

    @public
    def get_sensor_def(self, name: str) -> SensorDefinition:
        """Get a :py:class:`SensorDefinition` by name.
        If your passed-in sensor had resource dependencies, or the job targeted by the sensor had
        resource dependencies, those resource dependencies will be fully resolved on the returned object.
        """
        check.str_param(name, "name")
        return self.get_repository_def().get_sensor_def(name)

    @public
    def get_schedule_def(self, name: str) -> ScheduleDefinition:
        """Get a :py:class:`ScheduleDefinition` by name.
        If your passed-in schedule had resource dependencies, or the job targeted by the schedule had
        resource dependencies, those resource dependencies will be fully resolved on the returned object.
        """
        check.str_param(name, "name")
        return self.get_repository_def().get_schedule_def(name)

    @public
    def load_asset_value(
        self,
        asset_key: CoercibleToAssetKey,
        *,
        python_type: Optional[Type] = None,
        instance: Optional[DagsterInstance] = None,
        partition_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
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

    def get_all_job_defs(self) -> Sequence[JobDefinition]:
        """Get all the Job definitions in the code location.
        This includes both jobs passed into the Definitions object and any implicit jobs created.
        All jobs returned from this function will have all resource dependencies resolved.
        """
        return self.get_repository_def().get_all_jobs()

    def has_implicit_global_asset_job_def(self) -> bool:
        return self.get_repository_def().has_implicit_global_asset_job_def()

    def get_implicit_global_asset_job_def(self) -> JobDefinition:
        """A useful conveninence method when there is a single defined global asset job.
        This occurs when all assets in the code location use a single partitioning scheme.
        If there are multiple partitioning schemes you must use get_implicit_job_def_for_assets
        instead to access to the correct implicit asset one.
        """
        return self.get_repository_def().get_implicit_global_asset_job_def()

    def get_implicit_job_def_for_assets(
        self, asset_keys: Iterable[AssetKey]
    ) -> Optional[JobDefinition]:
        return self.get_repository_def().get_implicit_job_def_for_assets(asset_keys)

    def get_assets_def(self, key: CoercibleToAssetKey) -> AssetsDefinition:
        asset_key = AssetKey.from_coercible(key)
        for assets_def in self.get_asset_graph().assets_defs:
            if asset_key in assets_def.keys:
                return assets_def

        raise DagsterInvariantViolationError(f"Could not find asset {asset_key}")

    @cached_method
    def get_repository_def(self) -> RepositoryDefinition:
        """Definitions is implemented by wrapping RepositoryDefinition. Get that underlying object
        in order to access any functionality which is not exposed on Definitions. This method
        also resolves a PendingRepositoryDefinition to a RepositoryDefinition.
        """
        inner_repository = self.get_inner_repository()
        return (
            inner_repository.compute_repository_definition()
            if isinstance(inner_repository, PendingRepositoryDefinition)
            else inner_repository
        )

    @cached_method
    def get_inner_repository(
        self,
    ) -> Union[RepositoryDefinition, PendingRepositoryDefinition]:
        """This method is used internally to access the inner repository. We explicitly do not want
        to resolve the pending repo because the entire point is to defer that resolution until
        later.
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
        )

    def get_asset_graph(self) -> AssetGraph:
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

        Meant to be used in unit tests.

        Raises an error if any of the above are not true.
        """
        defs.get_repository_def().load_all_definitions()

    @public
    @experimental
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

        resources = {}
        resource_key_indexes: Dict[str, int] = {}
        loggers = {}
        logger_key_indexes: Dict[str, int] = {}
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
        )

    @public
    @experimental
    def get_all_asset_specs(self) -> Sequence[AssetSpec]:
        """Returns an AssetSpec object for every asset contained inside the Definitions object."""
        asset_graph = self.get_asset_graph()
        return [asset_node.to_asset_spec() for asset_node in asset_graph.asset_nodes]

    @experimental
    def with_reconstruction_metadata(self, reconstruction_metadata: Mapping[str, str]) -> Self:
        """Add reconstruction metadata to the Definitions object. This is typically used to cache data
        loaded from some external API that is computed during initialization of a code server.
        The cached data is then made available on the DefinitionsLoadContext during
        reconstruction of the same code location context (such as a run worker), allowing use of the
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
