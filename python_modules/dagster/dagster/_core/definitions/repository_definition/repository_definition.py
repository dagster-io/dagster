from typing import (
    TYPE_CHECKING,
    AbstractSet,
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

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions.asset_graph import AssetGraph, InternalAssetGraph
from dagster._core.definitions.assets_job import (
    ASSET_BASE_JOB_PREFIX,
)
from dagster._core.definitions.cacheable_assets import AssetsDefinitionCacheableData
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.executor_definition import ExecutorDefinition
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.logger_definition import LoggerDefinition
from dagster._core.definitions.metadata import MetadataMapping
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.schedule_definition import ScheduleDefinition
from dagster._core.definitions.sensor_definition import SensorDefinition
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.utils import check_valid_name
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.instance import DagsterInstance
from dagster._serdes import whitelist_for_serdes
from dagster._utils import hash_collection

from .repository_data import CachingRepositoryData, RepositoryData
from .valid_definitions import (
    RepositoryListDefinition as RepositoryListDefinition,
)

if TYPE_CHECKING:
    from dagster._core.definitions import AssetsDefinition
    from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition
    from dagster._core.storage.asset_value_loader import AssetValueLoader


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
            cached_data_by_key=(
                check.mapping_param(
                    cached_data_by_key,
                    "cached_data_by_key",
                    key_type=str,
                    value_type=list,
                )
            ),
        )

    # Allow this to be hashed for use in `lru_cache`. This is needed because:
    # - `ReconstructableJob` uses `lru_cache`
    # - `ReconstructableJob` has a `ReconstructableRepository` attribute
    # - `ReconstructableRepository` has a `RepositoryLoadData` attribute
    # - `RepositoryLoadData` has collection attributes that are unhashable by default
    def __hash__(self) -> int:
        if not hasattr(self, "_hash"):
            self._hash = hash_collection(self)
        return self._hash


class RepositoryDefinition:
    """Define a repository that contains a group of definitions.

    Users should typically not create objects of this class directly. Instead, use the
    :py:func:`@repository` decorator.

    Args:
        name (str): The name of the repository.
        repository_data (RepositoryData): Contains the definitions making up the repository.
        description (Optional[str]): A string description of the repository.
        metadata (Optional[MetadataMapping]): A map of arbitrary metadata for the repository.
    """

    def __init__(
        self,
        name,
        *,
        repository_data,
        description=None,
        metadata=None,
        repository_load_data=None,
    ):
        self._name = check_valid_name(name)
        self._description = check.opt_str_param(description, "description")
        self._repository_data: RepositoryData = check.inst_param(
            repository_data, "repository_data", RepositoryData
        )
        self._metadata = check.opt_mapping_param(metadata, "metadata", key_type=str)
        self._repository_load_data = check.opt_inst_param(
            repository_load_data, "repository_load_data", RepositoryLoadData
        )

    @property
    def repository_load_data(self) -> Optional[RepositoryLoadData]:
        return self._repository_load_data

    @public
    @property
    def name(self) -> str:
        """str: The name of the repository."""
        return self._name

    @public
    @property
    def description(self) -> Optional[str]:
        """Optional[str]: A human-readable description of the repository."""
        return self._description

    @public
    @property
    def metadata(self) -> Optional[MetadataMapping]:
        """Optional[MetadataMapping]: Arbitrary metadata for the repository."""
        return self._metadata

    def load_all_definitions(self):
        # force load of all lazy constructed code artifacts
        self._repository_data.load_all_definitions()

    @public
    @property
    def job_names(self) -> Sequence[str]:
        """List[str]: Names of all jobs in the repository."""
        return self._repository_data.get_job_names()

    def get_top_level_resources(self) -> Mapping[str, ResourceDefinition]:
        return self._repository_data.get_top_level_resources()

    def get_env_vars_by_top_level_resource(self) -> Mapping[str, AbstractSet[str]]:
        return self._repository_data.get_env_vars_by_top_level_resource()

    def get_resource_key_mapping(self) -> Mapping[int, str]:
        return self._repository_data.get_resource_key_mapping()

    @public
    def has_job(self, name: str) -> bool:
        """Check if a job with a given name is present in the repository.

        Args:
            name (str): The name of the job.

        Returns:
            bool
        """
        return self._repository_data.has_job(name)

    @public
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

    @public
    @property
    def schedule_defs(self) -> Sequence[ScheduleDefinition]:
        """List[ScheduleDefinition]: All schedules in the repository."""
        return self._repository_data.get_all_schedules()

    @public
    def get_schedule_def(self, name: str) -> ScheduleDefinition:
        """Get a schedule definition by name.

        Args:
            name (str): The name of the schedule.

        Returns:
            ScheduleDefinition: The schedule definition.
        """
        return self._repository_data.get_schedule(name)

    @public
    def has_schedule_def(self, name: str) -> bool:
        """bool: Check if a schedule with a given name is present in the repository."""
        return self._repository_data.has_schedule(name)

    @public
    @property
    def sensor_defs(self) -> Sequence[SensorDefinition]:
        """Sequence[SensorDefinition]: All sensors in the repository."""
        return self._repository_data.get_all_sensors()

    @public
    def get_sensor_def(self, name: str) -> SensorDefinition:
        """Get a sensor definition by name.

        Args:
            name (str): The name of the sensor.

        Returns:
            SensorDefinition: The sensor definition.
        """
        return self._repository_data.get_sensor(name)

    @public
    def has_sensor_def(self, name: str) -> bool:
        """bool: Check if a sensor with a given name is present in the repository."""
        return self._repository_data.has_sensor(name)

    @property
    def source_assets_by_key(self) -> Mapping[AssetKey, SourceAsset]:
        return self._repository_data.get_source_assets_by_key()

    @property
    def assets_defs_by_key(self) -> Mapping[AssetKey, "AssetsDefinition"]:
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
        """Returns the asset base job that contains all the given assets, or None if there is no such
        job.
        """
        if self.has_job(ASSET_BASE_JOB_PREFIX):
            base_job = self.get_job(ASSET_BASE_JOB_PREFIX)
            if all(
                key in base_job.asset_layer.assets_defs_by_key
                or base_job.asset_layer.is_observable_for_asset(key)
                for key in asset_keys
            ):
                return base_job
        else:
            i = 0
            while self.has_job(f"{ASSET_BASE_JOB_PREFIX}_{i}"):
                base_job = self.get_job(f"{ASSET_BASE_JOB_PREFIX}_{i}")

                if all(
                    key in base_job.asset_layer.assets_defs_by_key
                    or base_job.asset_layer.is_observable_for_asset(key)
                    for key in asset_keys
                ):
                    return base_job

                i += 1

        return None

    def get_maybe_subset_job_def(
        self,
        job_name: str,
        op_selection: Optional[Iterable[str]] = None,
        asset_selection: Optional[AbstractSet[AssetKey]] = None,
    ):
        defn = self.get_job(job_name)
        return defn.get_subset(op_selection=op_selection, asset_selection=asset_selection)

    @public
    def load_asset_value(
        self,
        asset_key: CoercibleToAssetKey,
        *,
        python_type: Optional[Type] = None,
        instance: Optional[DagsterInstance] = None,
        partition_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        resource_config: Optional[Any] = None,
    ) -> object:
        """Load the contents of an asset as a Python object.

        Invokes `load_input` on the :py:class:`IOManager` associated with the asset.

        If you want to load the values of multiple assets, it's more efficient to use
        :py:meth:`~dagster.RepositoryDefinition.get_asset_value_loader`, which avoids spinning up
        resources separately for each asset.

        Args:
            asset_key (Union[AssetKey, Sequence[str], str]): The key of the asset to load.
            python_type (Optional[Type]): The python type to load the asset as. This is what will
                be returned inside `load_input` by `context.dagster_type.typing_type`.
            partition_key (Optional[str]): The partition of the asset to load.
            metadata (Optional[Dict[str, Any]]): Input metadata to pass to the :py:class:`IOManager`
                (is equivalent to setting the metadata argument in `In` or `AssetIn`).
            resource_config (Optional[Any]): A dictionary of resource configurations to be passed
                to the :py:class:`IOManager`.

        Returns:
            The contents of an asset as a Python object.
        """
        from dagster._core.storage.asset_value_loader import AssetValueLoader

        with AssetValueLoader(
            self.assets_defs_by_key, self.source_assets_by_key, instance=instance
        ) as loader:
            return loader.load_asset_value(
                asset_key,
                python_type=python_type,
                partition_key=partition_key,
                metadata=metadata,
                resource_config=resource_config,
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

            with my_repo.get_asset_value_loader() as loader:
                asset1 = loader.load_asset_value("asset1")
                asset2 = loader.load_asset_value("asset2")

        """
        from dagster._core.storage.asset_value_loader import AssetValueLoader

        return AssetValueLoader(
            self.assets_defs_by_key, self.source_assets_by_key, instance=instance
        )

    @property
    def asset_graph(self) -> InternalAssetGraph:
        return AssetGraph.from_assets(
            [*set(self.assets_defs_by_key.values()), *self.source_assets_by_key.values()]
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
        metadata: Optional[MetadataMapping] = None,
        default_logger_defs: Optional[Mapping[str, LoggerDefinition]] = None,
        default_executor_def: Optional[ExecutorDefinition] = None,
        _top_level_resources: Optional[Mapping[str, ResourceDefinition]] = None,
        _resource_key_mapping: Optional[Mapping[int, str]] = None,
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
        self._metadata = metadata
        self._default_logger_defs = default_logger_defs
        self._default_executor_def = default_executor_def
        self._top_level_resources = _top_level_resources
        self._resource_key_mapping = _resource_key_mapping

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
            top_level_resources=self._top_level_resources,
            resource_key_mapping=self._resource_key_mapping,
        )

        return RepositoryDefinition(
            self._name,
            repository_data=repository_data,
            description=self._description,
            metadata=self._metadata,
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
