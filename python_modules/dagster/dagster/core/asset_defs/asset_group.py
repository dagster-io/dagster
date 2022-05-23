import inspect
import os
import pkgutil
import warnings
from collections import defaultdict
from importlib import import_module
from types import ModuleType
from typing import (
    AbstractSet,
    Any,
    Dict,
    Generator,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
    cast,
)

import dagster._check as check
from dagster.core.definitions.dependency import NodeHandle
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.executor_definition import in_process_executor
from dagster.core.errors import DagsterUnmetExecutorRequirementsError
from dagster.core.execution.execute_in_process_result import ExecuteInProcessResult
from dagster.core.storage.fs_asset_io_manager import fs_asset_io_manager
from dagster.utils import merge_dicts
from dagster.utils.backcompat import ExperimentalWarning

from ..definitions.executor_definition import ExecutorDefinition
from ..definitions.job_definition import JobDefinition
from ..definitions.partition import PartitionsDefinition
from ..definitions.resource_definition import ResourceDefinition
from ..errors import DagsterInvalidDefinitionError
from .assets import AssetsDefinition
from .assets_job import build_assets_job, build_root_manager, build_source_assets_by_key
from .source_asset import SourceAsset

ASSET_GROUP_BASE_JOB_PREFIX = "__ASSET_GROUP"


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
        executor_def = check.opt_inst_param(executor_def, "executor_def", ExecutorDefinition)

        if "root_manager" in resource_defs:
            raise DagsterInvalidDefinitionError(
                "Resource dictionary included resource with key 'root_manager', "
                "which is a reserved resource keyword in Dagster. Please change "
                "this key, and then change all places that require this key to "
                "a new value."
            )
        # In the case of collisions, merge_dicts takes values from the
        # dictionary latest in the list, so we place the user provided resource
        # defs after the defaults.
        resource_defs = merge_dicts({"io_manager": fs_asset_io_manager}, resource_defs)

        _validate_resource_reqs_for_asset_group(
            asset_list=assets, source_assets=source_assets, resource_defs=resource_defs
        )

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
        return name.startswith(ASSET_GROUP_BASE_JOB_PREFIX)

    def build_job(
        self,
        name: str,
        selection: Optional[Union[str, List[str]]] = None,
        executor_def: Optional[ExecutorDefinition] = None,
        tags: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
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

        from dagster.core.selector.subset_selector import parse_asset_selection

        check.str_param(name, "name")

        if not isinstance(selection, str):
            selection = check.opt_list_param(selection, "selection", of_type=str)
        else:
            selection = [selection]
        executor_def = check.opt_inst_param(
            executor_def, "executor_def", ExecutorDefinition, self.executor_def
        )
        description = check.opt_str_param(description, "description")
        resource_defs = build_resource_defs(self.resource_defs, self.source_assets)

        if selection:
            selected_asset_keys = parse_asset_selection(self.assets, selection)
            included_assets, excluded_assets = self._subset_assets_defs(selected_asset_keys)
        else:
            included_assets = cast(List[AssetsDefinition], self.assets)
            # Call to list(...) serves as a copy constructor, so that we don't
            # accidentally add to the original list
            excluded_assets = list(self.source_assets)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=ExperimentalWarning)
            asset_job = build_assets_job(
                name=name,
                assets=included_assets,
                source_assets=excluded_assets,
                resource_defs=resource_defs,
                executor_def=executor_def,
                description=description,
                tags=tags,
            )
        return asset_job

    def _subset_assets_defs(
        self, selected_asset_keys: AbstractSet[AssetKey]
    ) -> Tuple[Sequence[AssetsDefinition], Sequence[AssetsDefinition]]:
        """Given a list of asset key selection queries, generate a set of AssetsDefinition objects
        representing the included/excluded definitions.
        """
        included_assets: Set[AssetsDefinition] = set()
        excluded_assets: Set[AssetsDefinition] = set()

        for asset in self.assets:
            # intersection
            selected_subset = selected_asset_keys & asset.asset_keys
            # all assets in this def are selected
            if selected_subset == asset.asset_keys:
                included_assets.add(asset)
            # no assets in this def are selected
            elif len(selected_subset) == 0:
                excluded_assets.add(asset)
            elif asset.can_subset:
                # subset of the asset that we want
                subset_asset = asset.subset_for(selected_asset_keys)
                included_assets.add(subset_asset)
                # subset of the asset that we don't want
                excluded_assets.add(asset.subset_for(asset.asset_keys - subset_asset.asset_keys))
            else:
                raise DagsterInvalidDefinitionError(
                    f"When building job, the AssetsDefinition '{asset.node_def.name}' "
                    f"contains asset keys {sorted(list(asset.asset_keys))}, but "
                    f"attempted to select only {sorted(list(selected_subset))}. "
                    "This AssetsDefinition does not support subsetting. Please select all "
                    "asset keys produced by this asset."
                )
        return list(included_assets), list(excluded_assets)

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
        return AssetGroup.from_modules(
            _find_modules_in_package(package_module),
            resource_defs=resource_defs,
            executor_def=executor_def,
            extra_source_assets=extra_source_assets,
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
        asset_ids: Set[int] = set()
        asset_keys: Dict[AssetKey, ModuleType] = dict()
        source_assets: List[SourceAsset] = list(
            check.opt_sequence_param(
                extra_source_assets, "extra_source_assets", of_type=SourceAsset
            )
        )
        assets: List[AssetsDefinition] = []
        for module in modules:
            for asset in _find_assets_in_module(module):
                if id(asset) not in asset_ids:
                    asset_ids.add(id(asset))
                    keys = asset.asset_keys if isinstance(asset, AssetsDefinition) else [asset.key]
                    for key in keys:
                        if key in asset_keys:
                            modules_str = ", ".join(
                                set([asset_keys[key].__name__, module.__name__])
                            )
                            raise DagsterInvalidDefinitionError(
                                f"Asset key {key} is defined multiple times. Definitions found in modules: {modules_str}."
                            )
                        else:
                            asset_keys[key] = module
                    if isinstance(asset, SourceAsset):
                        source_assets.append(asset)
                    else:
                        assets.append(asset)

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
        self, selection: Optional[Union[str, List[str]]] = None
    ) -> ExecuteInProcessResult:
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
        ).execute_in_process()

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
                return [self.build_job(ASSET_GROUP_BASE_JOB_PREFIX)]
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
                                f"{ASSET_GROUP_BASE_JOB_PREFIX}_{i}",
                                assets=assets_with_partitions + unpartitioned_assets,
                                source_assets=[*self.source_assets, *self.assets],
                                resource_defs={
                                    **self.resource_defs,
                                    "root_manager": build_root_manager(
                                        build_source_assets_by_key(self.source_assets)
                                    ),
                                },
                                executor_def=self.executor_def,
                            )
                        )

                return jobs

    def prefixed(self, key_prefix: str):
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
                assert result.assets[0].asset_key == AssetKey(["my_prefix", "asset1"])

        Example with dependencies within the list of assets:

            .. code-block:: python

                @asset
                def asset1():
                    ...

                @asset
                def asset2(asset1):
                    ...

                result = AssetGroup([asset1, asset2]).prefixed("my_prefix")
                assert result.assets[0].asset_key == AssetKey(["my_prefix", "asset1"])
                assert result.assets[1].asset_key == AssetKey(["my_prefix", "asset2"])
                assert result.assets[1].dependency_asset_keys == {AssetKey(["my_prefix", "asset1"])}

        Examples with input prefixes provided by source assets:

            .. code-block:: python

                asset1 = SourceAsset(AssetKey(["upstream_prefix", "asset1"]))

                @asset
                def asset2(asset1):
                    ...

                result = AssetGroup([asset2], source_assets=[asset1]).prefixed("my_prefix")
                assert len(result.assets) == 1
                assert result.assets[0].asset_key == AssetKey(["my_prefix", "asset2"])
                assert result.assets[0].dependency_asset_keys == {AssetKey(["upstream_prefix", "asset1"])}
                assert result.source_assets[0].key == AssetKey(["upstream_prefix", "asset1"])
        """

        asset_keys = {
            asset_key for assets_def in self.assets for asset_key in assets_def.asset_keys
        }

        result_assets: List[AssetsDefinition] = []
        for assets_def in self.assets:
            output_asset_key_replacements = {
                asset_key: AssetKey([key_prefix] + asset_key.path)
                for asset_key in assets_def.asset_keys
            }
            input_asset_key_replacements = {}
            for dep_asset_key in assets_def.dependency_asset_keys:
                if dep_asset_key in asset_keys:
                    input_asset_key_replacements[dep_asset_key] = AssetKey(
                        (key_prefix, *dep_asset_key.path)
                    )

            result_assets.append(
                assets_def.with_replaced_asset_keys(
                    output_asset_key_replacements=output_asset_key_replacements,
                    input_asset_key_replacements=input_asset_key_replacements,
                )
            )

        return AssetGroup(
            assets=result_assets,
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


def build_resource_defs(resource_defs, source_assets):
    return {
        **resource_defs,
        **{"root_manager": build_root_manager(build_source_assets_by_key(source_assets))},
    }


def _find_assets_in_module(
    module: ModuleType,
) -> Generator[Union[AssetsDefinition, SourceAsset], None, None]:
    """
    Finds assets in the given module and adds them to the given sets of assets and source assets.
    """
    for attr in dir(module):
        value = getattr(module, attr)
        if isinstance(value, (AssetsDefinition, SourceAsset)):
            yield value
        elif isinstance(value, list) and all(
            isinstance(el, (AssetsDefinition, SourceAsset)) for el in value
        ):
            yield from value


def _find_modules_in_package(package_module: ModuleType) -> Iterable[ModuleType]:
    yield package_module
    package_path = package_module.__file__
    if package_path:
        for _, modname, is_pkg in pkgutil.walk_packages([os.path.dirname(package_path)]):
            submodule = import_module(f"{package_module.__name__}.{modname}")
            if is_pkg:
                yield from _find_modules_in_package(submodule)
            else:
                yield submodule
    else:
        raise ValueError(
            f"Tried to find modules in package {package_module}, but its __file__ is None"
        )


def _validate_resource_reqs_for_asset_group(
    asset_list: Sequence[AssetsDefinition],
    source_assets: Sequence[SourceAsset],
    resource_defs: Mapping[str, ResourceDefinition],
):
    present_resource_keys = set(resource_defs.keys())
    for asset_def in asset_list:
        resource_keys: Set[str] = set()
        for op_def in asset_def.node_def.iterate_solid_defs():
            resource_keys.update(set(op_def.required_resource_keys or {}))
        missing_resource_keys = list(set(resource_keys) - present_resource_keys)
        if missing_resource_keys:
            raise DagsterInvalidDefinitionError(
                f"AssetGroup is missing required resource keys for asset '{asset_def.node_def.name}'. "
                f"Missing resource keys: {missing_resource_keys}"
            )

        for output_name, asset_key in asset_def.asset_keys_by_output_name.items():
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
