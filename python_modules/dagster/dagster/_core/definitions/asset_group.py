import inspect
import warnings
from collections import defaultdict
from importlib import import_module
from types import ModuleType
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    FrozenSet,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Union,
)

import dagster._check as check
from dagster._core.definitions.dependency import NodeHandle
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKeyPrefix
from dagster._core.definitions.executor_definition import in_process_executor
from dagster._core.definitions.utils import DEFAULT_IO_MANAGER_KEY
from dagster._core.errors import (
    DagsterInvalidDefinitionError,
    DagsterUnmetExecutorRequirementsError,
)
from dagster._core.selector.subset_selector import AssetSelectionData
from dagster._core.storage.fs_io_manager import fs_io_manager
from dagster._utils import merge_dicts
from dagster._utils.backcompat import ExperimentalWarning

from .asset_layer import build_asset_selection_job
from .assets import AssetsDefinition
from .assets_job import build_assets_job, check_resources_satisfy_requirements
from .dependency import NodeHandle
from .events import AssetKey, CoercibleToAssetKeyPrefix
from .executor_definition import ExecutorDefinition, in_process_executor
from .job_definition import JobDefinition
from .load_assets_from_modules import (
    assets_and_source_assets_from_modules,
    assets_and_source_assets_from_package_module,
    prefix_assets,
)
from .partition import PartitionsDefinition
from .resource_definition import ResourceDefinition
from .source_asset import SourceAsset

if TYPE_CHECKING:
    from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult

# Prefix for auto created jobs that are used to materialize assets
ASSET_BASE_JOB_PREFIX = "__ASSET_JOB"


class AssetGroup:
    """Defines a group of assets, along with environment information in the
    form of resources and an executor.

    An AssetGroup can be provided to a :py:class:`RepositoryDefinition`. When
    provided to a repository, the constituent assets can be materialized from
    Dagit. The AssetGroup also provides an interface for creating jobs from
    subselections of assets, which can then be provided to a
    :py:class:`ScheduleDefinition` or :py:class:`SensorDefinition`.

    There can only be one AssetGroup per repository.

    Args:
        assets (Sequence[AssetsDefinition]): The set of software-defined assets
            to group.
        source_assets (Optional[Sequence[SourceAsset]]): The set of source
            assets that the software-defined may depend on.
        resource_defs (Optional[Mapping[str, ResourceDefinition]]): A
            dictionary of resource definitions. When the AssetGroup is
            constructed, if there are any unsatisfied resource requirements
            from the assets, it will result in an error. Note that the
            `root_manager` key is a reserved resource key, and will result in
            an error if provided by the user.
        executor_def (Optional[ExecutorDefinition]): The executor definition to
            use when re-materializing assets in this group.

    Examples:

        .. code-block:: python

            from dagster import AssetGroup, asset, AssetIn, AssetKey, SourceAsset, resource

            source_asset = SourceAsset("source")

            @asset(required_resource_keys={"foo"})
            def start_asset(context, source):
                ...

            @asset
            def next_asset(start_asset):
                ...

            @resource
            def foo_resource():
                ...

            asset_group = AssetGroup(
                assets=[start_asset, next_asset],
                source_assets=[source_asset],
                resource_defs={"foo": foo_resource},
            )
            ...

    """

    def __init__(
        self,
        assets: Sequence[AssetsDefinition],
        source_assets: Optional[Sequence[SourceAsset]] = None,
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
        executor_def: Optional[ExecutorDefinition] = None,
    ):
        check.sequence_param(assets, "assets", of_type=AssetsDefinition)

        source_assets = check.opt_sequence_param(
            source_assets, "source_assets", of_type=SourceAsset
        )
        resource_defs = check.opt_mapping_param(
            resource_defs, "resource_defs", key_type=str, value_type=ResourceDefinition
        )
        resource_defs = merge_dicts({DEFAULT_IO_MANAGER_KEY: fs_io_manager}, resource_defs)
        executor_def = check.opt_inst_param(executor_def, "executor_def", ExecutorDefinition)

        check_resources_satisfy_requirements(assets, source_assets, resource_defs)

        self._assets = assets
        self._source_assets = source_assets
        self._resource_defs = resource_defs
        self._executor_def = executor_def

    @property
    def assets(self):
        return self._assets

    @property
    def source_assets(self):
        return self._source_assets

    @property
    def resource_defs(self):
        return self._resource_defs

    @property
    def executor_def(self):
        return self._executor_def

    @staticmethod
    def is_base_job_name(name) -> bool:
        return name.startswith(ASSET_BASE_JOB_PREFIX)

    def build_job(
        self,
        name: str,
        selection: Optional[Union[str, List[str]]] = None,
        executor_def: Optional[ExecutorDefinition] = None,
        tags: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        _asset_selection_data: Optional[AssetSelectionData] = None,
    ) -> JobDefinition:
        """Defines an executable job from the provided assets, resources, and executor.

        Args:
            name (str): The name to give the job.
            selection (Union[str, List[str]]): A single selection query or list of selection queries
                to execute. For example:

                    - ``['some_asset_key']`` select ``some_asset_key`` itself.
                    - ``['*some_asset_key']`` select ``some_asset_key`` and all its ancestors (upstream dependencies).
                    - ``['*some_asset_key+++']`` select ``some_asset_key``, all its ancestors, and its descendants (downstream dependencies) within 3 levels down.
                    - ``['*some_asset_key', 'other_asset_key_a', 'other_asset_key_b+']`` select ``some_asset_key`` and all its ancestors, ``other_asset_key_a`` itself, and ``other_asset_key_b`` and its direct child asset keys. When subselecting into a multi-asset, all of the asset keys in that multi-asset must be selected.

            executor_def (Optional[ExecutorDefinition]): The executor
                definition to use when executing the job. Defaults to the
                executor on the AssetGroup. If no executor was provided on the
                AssetGroup, then it defaults to :py:class:`multi_or_in_process_executor`.
            tags (Optional[Dict[str, Any]]): Arbitrary metadata for any execution of the job.
                Values that are not strings will be json encoded and must meet the criteria that
                `json.loads(json.dumps(value)) == value`.  These tag values may be overwritten
                tag values provided at invocation time.
            description (Optional[str]): A description of the job.

        Examples:

            .. code-block:: python

                from dagster import AssetGroup

                the_asset_group = AssetGroup(...)

                job_with_all_assets = the_asset_group.build_job()

                job_with_one_selection = the_asset_group.build_job(selection="some_asset")

                job_with_multiple_selections = the_asset_group.build_job(selection=["*some_asset", "other_asset++"])
        """

        from dagster._core.selector.subset_selector import parse_asset_selection

        check.str_param(name, "name")
        check.opt_inst_param(_asset_selection_data, "_asset_selection_data", AssetSelectionData)

        selected_asset_keys: FrozenSet[AssetKey] = frozenset()
        if isinstance(selection, str):
            selected_asset_keys = parse_asset_selection(
                self.assets, self.source_assets, [selection]
            )
        elif isinstance(selection, list):
            selection = check.opt_list_param(selection, "selection", of_type=str)
            selected_asset_keys = parse_asset_selection(self.assets, self.source_assets, selection)
        elif isinstance(selection, FrozenSet):
            check.opt_set_param(selection, "selection", of_type=AssetKey)
            selected_asset_keys = selection

        executor_def = check.opt_inst_param(
            executor_def, "executor_def", ExecutorDefinition, self.executor_def
        )
        description = check.opt_str_param(description, "description", "")
        tags = check.opt_dict_param(tags, "tags", key_type=str)

        return build_asset_selection_job(
            name=name,
            assets=self.assets,
            source_assets=self.source_assets,
            executor_def=executor_def,
            resource_defs=self.resource_defs,
            description=description,
            tags=tags,
            asset_selection=selected_asset_keys,
        )

    def to_source_assets(self) -> Sequence[SourceAsset]:
        """
        Returns a list of source assets corresponding to all the non-source assets in this group.
        """
        return [
            source_asset
            for assets_def in self.assets
            for source_asset in assets_def.to_source_assets()
        ]

    @staticmethod
    def from_package_module(
        package_module: ModuleType,
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
        executor_def: Optional[ExecutorDefinition] = None,
        extra_source_assets: Optional[Sequence[SourceAsset]] = None,
    ) -> "AssetGroup":
        """
        Constructs an AssetGroup that includes all asset definitions and source assets in all
        sub-modules of the given package module.

        A package module is the result of importing a package.

        Args:
            package_module (ModuleType): The package module to looks for assets inside.
            resource_defs (Optional[Mapping[str, ResourceDefinition]]): A dictionary of resource
                definitions to include on the returned asset group.
            executor_def (Optional[ExecutorDefinition]): An executor to include on the returned
                asset group.
            extra_source_assets (Optional[Sequence[SourceAsset]]): Source assets to include in the
                group in addition to the source assets found in the package.

        Returns:
            AssetGroup: An asset group with all the assets in the package.
        """
        assets, source_assets = assets_and_source_assets_from_package_module(
            package_module, extra_source_assets
        )
        return AssetGroup(
            assets=assets,
            source_assets=source_assets,
            resource_defs=resource_defs,
            executor_def=executor_def,
        )

    @staticmethod
    def from_package_name(
        package_name: str,
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
        executor_def: Optional[ExecutorDefinition] = None,
        extra_source_assets: Optional[Sequence[SourceAsset]] = None,
    ) -> "AssetGroup":
        """
        Constructs an AssetGroup that includes all asset definitions and source assets in all
        sub-modules of the given package.

        Args:
            package_name (str): The name of a Python package to look for assets inside.
            resource_defs (Optional[Mapping[str, ResourceDefinition]]): A dictionary of resource
                definitions to include on the returned asset group.
            executor_def (Optional[ExecutorDefinition]): An executor to include on the returned
                asset group.
            extra_source_assets (Optional[Sequence[SourceAsset]]): Source assets to include in the
                group in addition to the source assets found in the package.

        Returns:
            AssetGroup: An asset group with all the assets in the package.
        """
        package_module = import_module(package_name)
        return AssetGroup.from_package_module(
            package_module,
            resource_defs=resource_defs,
            executor_def=executor_def,
            extra_source_assets=extra_source_assets,
        )

    @staticmethod
    def from_modules(
        modules: Iterable[ModuleType],
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
        executor_def: Optional[ExecutorDefinition] = None,
        extra_source_assets: Optional[Sequence[SourceAsset]] = None,
    ) -> "AssetGroup":
        """
        Constructs an AssetGroup that includes all asset definitions and source assets in the given
        modules.

        Args:
            modules (Iterable[ModuleType]): The Python modules to look for assets inside.
            resource_defs (Optional[Mapping[str, ResourceDefinition]]): A dictionary of resource
                definitions to include on the returned asset group.
            executor_def (Optional[ExecutorDefinition]): An executor to include on the returned
                asset group.
            extra_source_assets (Optional[Sequence[SourceAsset]]): Source assets to include in the
                group in addition to the source assets found in the modules.

        Returns:
            AssetGroup: An asset group with all the assets defined in the given modules.
        """
        assets, source_assets = assets_and_source_assets_from_modules(modules, extra_source_assets)

        return AssetGroup(
            assets=assets,
            source_assets=source_assets,
            resource_defs=resource_defs,
            executor_def=executor_def,
        )

    @staticmethod
    def from_current_module(
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
        executor_def: Optional[ExecutorDefinition] = None,
        extra_source_assets: Optional[Sequence[SourceAsset]] = None,
    ) -> "AssetGroup":
        """
        Constructs an AssetGroup that includes all asset definitions and source assets in the module
        where this is called from.

        Args:
            resource_defs (Optional[Mapping[str, ResourceDefinition]]): A dictionary of resource
                definitions to include on the returned asset group.
            executor_def (Optional[ExecutorDefinition]): An executor to include on the returned
                asset group.
            extra_source_assets (Optional[Sequence[SourceAsset]]): Source assets to include in the
                group in addition to the source assets found in the module.

        Returns:
            AssetGroup: An asset group with all the assets defined in the module.
        """
        caller = inspect.stack()[1]
        module = inspect.getmodule(caller[0])
        if module is None:
            check.failed("Could not find a module for the caller")
        return AssetGroup.from_modules(
            [module], resource_defs, executor_def, extra_source_assets=extra_source_assets
        )

    def materialize(
        self, selection: Optional[Union[str, List[str]]] = None, run_config: Optional[Any] = None
    ) -> "ExecuteInProcessResult":
        """
        Executes an in-process run that materializes all assets in the group.

        The execution proceeds serially, in a single thread. Only supported by AssetGroups that have
        no executor_def or that that use the in-process executor.

        Args:
            selection (Union[str, List[str]]): A single selection query or list of selection queries
                to for assets in the group. For example:

                    - ``['some_asset_key']`` select ``some_asset_key`` itself.
                    - ``['*some_asset_key']`` select ``some_asset_key`` and all its ancestors (upstream dependencies).
                    - ``['*some_asset_key+++']`` select ``some_asset_key``, all its ancestors, and its descendants (downstream dependencies) within 3 levels down.
                    - ``['*some_asset_key', 'other_asset_key_a', 'other_asset_key_b+']`` select ``some_asset_key`` and all its ancestors, ``other_asset_key_a`` itself, and ``other_asset_key_b`` and its direct child asset keys. When subselecting into a multi-asset, all of the asset keys in that multi-asset must be selected.
            run_config (Optional[Any]): The run config to use for the run that materializes the assets.

        Returns:
            ExecuteInProcessResult: The result of the execution.
        """
        if self.executor_def and self.executor_def is not in_process_executor:
            raise DagsterUnmetExecutorRequirementsError(
                "'materialize' can only be invoked on AssetGroups which have no executor or have "
                "the in_process_executor, but the AssetGroup had executor "
                f"'{self.executor_def.name}'"
            )

        return self.build_job(
            name="in_process_materialization_job", selection=selection
        ).execute_in_process(run_config=run_config)

    def get_base_jobs(self) -> Sequence[JobDefinition]:
        """For internal use only."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=ExperimentalWarning)

            assets_by_partitions_def: Dict[
                Optional[PartitionsDefinition], List[AssetsDefinition]
            ] = defaultdict(list)
            for assets_def in self.assets:
                assets_by_partitions_def[assets_def.partitions_def].append(assets_def)

            if len(assets_by_partitions_def.keys()) == 0 or assets_by_partitions_def.keys() == {
                None
            }:
                return [self.build_job(ASSET_BASE_JOB_PREFIX)]
            else:
                unpartitioned_assets = assets_by_partitions_def.get(None, [])
                jobs = []

                # sort to ensure some stability in the ordering
                for i, (partitions_def, assets_with_partitions) in enumerate(
                    sorted(assets_by_partitions_def.items(), key=lambda item: repr(item[0]))
                ):
                    if partitions_def is not None:
                        jobs.append(
                            build_assets_job(
                                f"{ASSET_BASE_JOB_PREFIX}_{i}",
                                assets=assets_with_partitions + unpartitioned_assets,
                                source_assets=[*self.source_assets, *self.assets],
                                resource_defs=self.resource_defs,
                                executor_def=self.executor_def,
                            )
                        )

                return jobs

    def prefixed(self, key_prefix: CoercibleToAssetKeyPrefix):
        """
        Returns an AssetGroup that's identical to this AssetGroup, but with prefixes on all the
        asset keys. The prefix is not added to source assets.

        Input asset keys that reference other assets within the group are "brought along" -
        i.e. prefixed as well.

        Example with a single asset:

            .. code-block:: python

                @asset
                def asset1():
                    ...

                result = AssetGroup([asset1]).prefixed("my_prefix")
                assert result.assets[0].key == AssetKey(["my_prefix", "asset1"])

        Example with dependencies within the list of assets:

            .. code-block:: python

                @asset
                def asset1():
                    ...

                @asset
                def asset2(asset1):
                    ...

                result = AssetGroup([asset1, asset2]).prefixed("my_prefix")
                assert result.assets[0].key == AssetKey(["my_prefix", "asset1"])
                assert result.assets[1].key == AssetKey(["my_prefix", "asset2"])
                assert result.assets[1].dependency_keys == {AssetKey(["my_prefix", "asset1"])}

        Examples with input prefixes provided by source assets:

            .. code-block:: python

                asset1 = SourceAsset(AssetKey(["upstream_prefix", "asset1"]))

                @asset
                def asset2(asset1):
                    ...

                result = AssetGroup([asset2], source_assets=[asset1]).prefixed("my_prefix")
                assert len(result.assets) == 1
                assert result.assets[0].key == AssetKey(["my_prefix", "asset2"])
                assert result.assets[0].dependency_keys == {AssetKey(["upstream_prefix", "asset1"])}
                assert result.source_assets[0].key == AssetKey(["upstream_prefix", "asset1"])
        """
        prefixed_assets = prefix_assets(self.assets, key_prefix)

        return AssetGroup(
            assets=prefixed_assets,
            source_assets=self.source_assets,
            resource_defs=self.resource_defs,
            executor_def=self.executor_def,
        )

    def __add__(self, other: "AssetGroup") -> "AssetGroup":
        check.inst_param(other, "other", AssetGroup)

        if self.resource_defs != other.resource_defs:
            raise DagsterInvalidDefinitionError(
                "Can't add asset groups together with different resource definition dictionaries"
            )

        if self.executor_def != other.executor_def:
            raise DagsterInvalidDefinitionError(
                "Can't add asset groups together with different executor definitions"
            )

        return AssetGroup(
            assets=self.assets + other.assets,
            source_assets=self.source_assets + other.source_assets,
            resource_defs=self.resource_defs,
            executor_def=self.executor_def,
        )

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, AssetGroup)
            and self.assets == other.assets
            and self.source_assets == other.source_assets
            and self.resource_defs == other.resource_defs
            and self.executor_def == other.executor_def
        )


def _validate_resource_reqs_for_asset_group(
    asset_list: Sequence[AssetsDefinition],
    source_assets: Sequence[SourceAsset],
    resource_defs: Mapping[str, ResourceDefinition],
):
    present_resource_keys = set(resource_defs.keys())
    for asset_def in asset_list:
        provided_resource_keys = set(asset_def.resource_defs.keys())
        present_resource_keys = present_resource_keys.union(provided_resource_keys)

        required_resource_keys: Set[str] = set()
        for op_def in asset_def.node_def.iterate_solid_defs():
            required_resource_keys.update(set(op_def.required_resource_keys or {}))
        missing_resource_keys = list(set(required_resource_keys) - present_resource_keys)
        if missing_resource_keys:
            raise DagsterInvalidDefinitionError(
                f"AssetGroup is missing required resource keys for asset '{asset_def.node_def.name}'. "
                f"Missing resource keys: {missing_resource_keys}"
            )

        for output_name, asset_key in asset_def.keys_by_output_name.items():
            output_def, _ = asset_def.node_def.resolve_output_to_origin(
                output_name, NodeHandle(name=asset_def.node_def.name, parent=None)
            )
            if output_def.io_manager_key and output_def.io_manager_key not in present_resource_keys:
                raise DagsterInvalidDefinitionError(
                    f"Output '{output_def.name}' with AssetKey '{asset_key}' "
                    f"requires io manager '{output_def.io_manager_key}' but was "
                    f"not provided on asset group. Provided resources: {sorted(list(present_resource_keys))}"
                )

    for source_asset in source_assets:
        if source_asset.io_manager_key and source_asset.io_manager_key not in present_resource_keys:
            raise DagsterInvalidDefinitionError(
                f"SourceAsset with key {source_asset.key} requires io manager "
                f"with key '{source_asset.io_manager_key}', which was not "
                f"provided on AssetGroup. Provided keys: {sorted(list(present_resource_keys))}"
            )

    for resource_key, resource_def in resource_defs.items():
        resource_keys = set(resource_def.required_resource_keys)
        missing_resource_keys = sorted(list(set(resource_keys) - present_resource_keys))
        if missing_resource_keys:
            raise DagsterInvalidDefinitionError(
                "AssetGroup is missing required resource keys for resource '"
                f"{resource_key}'. Missing resource keys: {missing_resource_keys}"
            )
