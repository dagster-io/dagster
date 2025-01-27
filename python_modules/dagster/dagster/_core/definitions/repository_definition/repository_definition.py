from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, AbstractSet, Any, NamedTuple, Optional  # noqa: UP035

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_job import IMPLICIT_ASSET_JOB_NAME
from dagster._core.definitions.cacheable_assets import AssetsDefinitionCacheableData
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.metadata import MetadataMapping
from dagster._core.definitions.metadata.metadata_value import (
    CodeLocationReconstructionMetadataValue,
)
from dagster._core.definitions.repository_definition.repository_data import RepositoryData
from dagster._core.definitions.repository_definition.valid_definitions import (
    RepositoryElementDefinition as RepositoryElementDefinition,
)
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.schedule_definition import ScheduleDefinition
from dagster._core.definitions.sensor_definition import SensorDefinition
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.utils import check_valid_name
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.instance import DagsterInstance
from dagster._serdes import whitelist_for_serdes
from dagster._utils import hash_collection
from dagster._utils.cached_method import cached_method

if TYPE_CHECKING:
    from dagster._core.definitions import AssetsDefinition
    from dagster._core.definitions.asset_checks import AssetChecksDefinition
    from dagster._core.storage.asset_value_loader import AssetValueLoader


@whitelist_for_serdes(
    storage_field_names={"cacheable_asset_data": "cached_data_by_key"},
)
class RepositoryLoadData(
    NamedTuple(
        "_RepositoryLoadData",
        [
            ("cacheable_asset_data", Mapping[str, Sequence[AssetsDefinitionCacheableData]]),
            ("reconstruction_metadata", Mapping[str, Any]),
        ],
    )
):
    def __new__(
        cls,
        cacheable_asset_data: Optional[
            Mapping[str, Sequence[AssetsDefinitionCacheableData]]
        ] = None,
        reconstruction_metadata: Optional[
            Mapping[str, CodeLocationReconstructionMetadataValue]
        ] = None,
    ):
        return super().__new__(
            cls,
            cacheable_asset_data=(
                check.opt_mapping_param(
                    cacheable_asset_data,
                    "cacheable_asset_data",
                    key_type=str,
                    value_type=list,
                )
            ),
            reconstruction_metadata=check.opt_mapping_param(
                reconstruction_metadata, "reconstruction_metadata", key_type=str
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

    def replace_reconstruction_metadata(
        self, reconstruction_metadata: Mapping[str, Any]
    ) -> "RepositoryLoadData":
        return RepositoryLoadData(
            cacheable_asset_data=self.cacheable_asset_data,
            reconstruction_metadata=reconstruction_metadata,
        )


class RepositoryDefinition:
    """Define a repository that contains a group of definitions.

    Users should typically not create objects of this class directly. Instead, use the
    :py:func:`@repository` decorator.

    Args:
        name (str): The name of the repository.
        repository_data (RepositoryData): Contains the definitions making up the repository.
        description (Optional[str]): A string description of the repository.
        metadata (Optional[MetadataMapping]): Arbitrary metadata for the repository. Not
            displayed in the UI but accessible on RepositoryDefinition at runtime.
    """

    def __init__(
        self,
        name: str,
        *,
        repository_data: RepositoryData,
        description: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        repository_load_data: Optional[RepositoryLoadData] = None,
    ):
        self._name = check_valid_name(name)
        self._description = check.opt_str_param(description, "description")
        self._repository_data = check.inst_param(repository_data, "repository_data", RepositoryData)
        self._metadata = check.opt_mapping_param(metadata, "metadata", key_type=str)
        self._repository_load_data = check.opt_inst_param(
            repository_load_data, "repository_load_data", RepositoryLoadData
        )

    @property
    def repository_load_data(self) -> Optional[RepositoryLoadData]:
        return self._repository_load_data

    def replace_reconstruction_metadata(
        self, reconstruction_metadata: Mapping[str, str]
    ) -> "RepositoryDefinition":
        """Modifies the repository load data to include the provided reconstruction metadata."""
        check.mapping_param(reconstruction_metadata, "reconstruction_metadata", key_type=str)
        if not reconstruction_metadata:
            return self

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
        return RepositoryDefinition(
            self._name,
            repository_data=self._repository_data,
            description=self._description,
            metadata=self._metadata,
            repository_load_data=self._repository_load_data.replace_reconstruction_metadata(
                normalized_metadata
            )
            if self._repository_load_data
            else RepositoryLoadData(reconstruction_metadata=normalized_metadata),
        )

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

    def load_all_definitions(self) -> None:
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

    @public
    @property
    def source_assets_by_key(self) -> Mapping[AssetKey, SourceAsset]:
        """Mapping[AssetKey, SourceAsset]: The source assets defined in the repository."""
        return self._repository_data.get_source_assets_by_key()

    # NOTE: `assets_defs_by_key` should generally not be used internally. It returns the
    # `AssetsDefinition` supplied at repository construction time. Internally, assets defs should be
    # obtained from the `AssetGraph` via `asset_graph.assets_defs`. This returns a normalized set of
    # assets defs, where:
    #
    # - `SourceAsset` instances are replaced with external `AssetsDefinition`
    # - Relative asset key dependencies are resolved
    # - External `AssetsDefinition` have been generated for referenced asset keys without a
    #   corresponding user-provided definition

    @public
    @property
    def assets_defs_by_key(self) -> Mapping[AssetKey, "AssetsDefinition"]:
        """Mapping[AssetKey, AssetsDefinition]: The assets definitions defined in the repository."""
        return self._repository_data.get_assets_defs_by_key()

    @public
    @property
    def asset_checks_defs_by_key(self) -> Mapping[AssetCheckKey, "AssetChecksDefinition"]:
        """Mapping[AssetCheckKey, AssetChecksDefinition]: The assets checks defined in the repository."""
        return self._repository_data.get_asset_checks_defs_by_key()

    def has_implicit_global_asset_job_def(self) -> bool:
        return self.has_job(IMPLICIT_ASSET_JOB_NAME)

    def get_implicit_global_asset_job_def(self) -> JobDefinition:
        return self.get_job(IMPLICIT_ASSET_JOB_NAME)

    def get_implicit_asset_job_names(self) -> Sequence[str]:
        return [IMPLICIT_ASSET_JOB_NAME]

    def get_implicit_job_def_for_assets(
        self, asset_keys: Iterable[AssetKey]
    ) -> Optional[JobDefinition]:
        return self.get_job(IMPLICIT_ASSET_JOB_NAME)

    def get_maybe_subset_job_def(
        self,
        job_name: str,
        op_selection: Optional[Iterable[str]] = None,
        asset_selection: Optional[AbstractSet[AssetKey]] = None,
        asset_check_selection: Optional[AbstractSet[AssetCheckKey]] = None,
    ):
        defn = self.get_job(job_name)
        return defn.get_subset(
            op_selection=op_selection,
            asset_selection=asset_selection,
            asset_check_selection=asset_check_selection,
        )

    @public
    def load_asset_value(
        self,
        asset_key: CoercibleToAssetKey,
        *,
        python_type: Optional[type] = None,
        instance: Optional[DagsterInstance] = None,
        partition_key: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
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

        # The normalized assets defs must be obtained from the asset graph, not the repository data
        normalized_assets_defs_by_key = {
            k: ad for ad in self.asset_graph.assets_defs for k in ad.keys
        }
        with AssetValueLoader(normalized_assets_defs_by_key, instance=instance) as loader:
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

        # The normalized assets defs must be obtained from the asset graph, not the repository data
        normalized_assets_defs_by_key = {
            k: ad for ad in self.asset_graph.assets_defs for k in ad.keys
        }
        return AssetValueLoader(normalized_assets_defs_by_key, instance=instance)

    @property
    @cached_method
    def asset_graph(self) -> AssetGraph:
        return AssetGraph.from_assets(
            [
                *list(set(self.assets_defs_by_key.values())),
                *self.source_assets_by_key.values(),
                *list(set(self.asset_checks_defs_by_key.values())),
            ],
        )

    # If definition comes from the @repository decorator, then the __call__ method will be
    # overwritten. Therefore, we want to maintain the call-ability of repository definitions.
    def __call__(self, *args, **kwargs):
        return self
