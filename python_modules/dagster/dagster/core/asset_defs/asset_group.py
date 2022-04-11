import inspect
import os
import pkgutil
import re
import warnings
from importlib import import_module
from types import ModuleType
from typing import (
    Any,
    Dict,
    Generator,
    Iterable,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Union,
    cast,
)

from dagster import check
from dagster.core.definitions.events import AssetKey
from dagster.core.execution.execute_in_process_result import ExecuteInProcessResult
from dagster.core.storage.fs_asset_io_manager import fs_asset_io_manager
from dagster.utils import merge_dicts
from dagster.utils.backcompat import ExperimentalWarning

from ..definitions.executor_definition import ExecutorDefinition
from ..definitions.job_definition import JobDefinition
from ..definitions.op_definition import OpDefinition
from ..definitions.resource_definition import ResourceDefinition
from ..errors import DagsterInvalidDefinitionError
from .assets import AssetsDefinition
from .assets_job import build_assets_job, build_root_manager, build_source_assets_by_key
from .source_asset import SourceAsset


class AssetGroup(
    NamedTuple(
        "_AssetGroup",
        [
            ("assets", Sequence[AssetsDefinition]),
            ("source_assets", Sequence[SourceAsset]),
            ("resource_defs", Mapping[str, ResourceDefinition]),
            ("executor_def", Optional[ExecutorDefinition]),
        ],
    )
):
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

    def __new__(
        cls,
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

        source_assets_by_key = build_source_assets_by_key(source_assets)
        root_manager = build_root_manager(source_assets_by_key)

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
        resource_defs = merge_dicts(
            {"root_manager": root_manager, "io_manager": fs_asset_io_manager},
            resource_defs,
        )

        _validate_resource_reqs_for_asset_group(
            asset_list=assets, source_assets=source_assets, resource_defs=resource_defs
        )

        return super(AssetGroup, cls).__new__(
            cls,
            assets=assets,
            source_assets=source_assets,
            resource_defs=resource_defs,
            executor_def=executor_def,
        )

    @staticmethod
    def all_assets_job_name() -> str:
        """The name of the mega-job that the provided list of assets is coerced into."""
        return "__ASSET_GROUP"

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

        from dagster.core.selector.subset_selector import parse_op_selection

        check.str_param(name, "name")

        if not isinstance(selection, str):
            selection = check.opt_list_param(selection, "selection", of_type=str)
        executor_def = check.opt_inst_param(executor_def, "executor_def", ExecutorDefinition)
        description = check.opt_str_param(description, "description")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=ExperimentalWarning)
            mega_job_def = build_assets_job(
                name=name,
                assets=self.assets,
                source_assets=self.source_assets,
                resource_defs=self.resource_defs,
                executor_def=self.executor_def,
            )

        if selection:
            op_selection = self._parse_asset_selection(selection, job_name=name)
            # We currently re-use the logic from op selection to parse the
            # asset key selection, but this has disadvantages. Eventually we
            # will want to decouple these implementations.
            # https://github.com/dagster-io/dagster/issues/6647.
            resolved_op_selection_dict = parse_op_selection(mega_job_def, op_selection)

            included_assets = []
            excluded_assets: List[Union[AssetsDefinition, SourceAsset]] = list(self.source_assets)

            op_names = set(list(resolved_op_selection_dict.keys()))

            for asset in self.assets:
                if asset.op.name in op_names:
                    included_assets.append(asset)
                else:
                    excluded_assets.append(asset)
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
                resource_defs=self.resource_defs,
                executor_def=self.executor_def,
                description=description,
                tags=tags,
            )
        return asset_job

    def _parse_asset_selection(self, selection: Union[str, List[str]], job_name: str) -> List[str]:
        """Convert selection over asset keys to selection over ops"""

        asset_keys_to_ops: Dict[str, List[OpDefinition]] = {}
        op_names_to_asset_keys: Dict[str, Set[str]] = {}
        seen_asset_keys: Set[str] = set()

        if isinstance(selection, str):
            selection = [selection]

        if len(selection) == 1 and selection[0] == "*":
            return selection

        source_asset_keys = set()

        for asset in self.assets:
            if asset.op.name not in op_names_to_asset_keys:
                op_names_to_asset_keys[asset.op.name] = set()
            for asset_key in asset.asset_keys:
                asset_key_as_str = ".".join([piece for piece in asset_key.path])
                op_names_to_asset_keys[asset.op.name].add(asset_key_as_str)
                if not asset_key_as_str in asset_keys_to_ops:
                    asset_keys_to_ops[asset_key_as_str] = []
                asset_keys_to_ops[asset_key_as_str].append(asset.op)

        for asset in self.source_assets:
            if isinstance(asset, SourceAsset):
                asset_key_as_str = ".".join([piece for piece in asset.key.path])
                source_asset_keys.add(asset_key_as_str)
            else:
                for asset_key in asset.asset_keys:
                    asset_key_as_str = ".".join([piece for piece in asset_key.path])
                    source_asset_keys.add(asset_key_as_str)

        op_selection = []

        for clause in selection:
            token_matching = re.compile(r"^(\*?\+*)?([.\w\d\[\]?_-]+)(\+*\*?)?$").search(
                clause.strip()
            )
            parts = token_matching.groups() if token_matching is not None else None
            if parts is None:
                raise DagsterInvalidDefinitionError(
                    f"When attempting to create job '{job_name}', the clause "
                    f"{clause} within the asset key selection was invalid. Please "
                    "review the selection syntax here: "
                    "https://docs.dagster.io/concepts/ops-jobs-graphs/job-execution#op-selection-syntax."
                )
            upstream_part, key_str, downstream_part = parts

            # Error if you express a clause in terms of a source asset key.
            # Eventually we will want to support selection over source asset
            # keys as a means of running downstream ops.
            # https://github.com/dagster-io/dagster/issues/6647
            if key_str in source_asset_keys:
                raise DagsterInvalidDefinitionError(
                    f"When attempting to create job '{job_name}', the clause '"
                    f"{clause}' selects asset_key '{key_str}', which comes from "
                    "a source asset. Source assets can't be materialized, and "
                    "therefore can't be subsetted into a job. Please choose a "
                    "subset on asset keys that are materializable - that is, "
                    f"included on assets within the group. Valid assets: {list(asset_keys_to_ops.keys())}"
                )
            if key_str not in asset_keys_to_ops:
                raise DagsterInvalidDefinitionError(
                    f"When attempting to create job '{job_name}', the clause "
                    f"'{clause}' within the asset key selection did not match "
                    f"any asset keys. Present asset keys: {list(asset_keys_to_ops.keys())}"
                )

            seen_asset_keys.add(key_str)

            for op in asset_keys_to_ops[key_str]:

                op_clause = f"{upstream_part}{op.name}{downstream_part}"
                op_selection.append(op_clause)

        # Verify that for each selected asset key, the corresponding op had all
        # asset keys selected. Eventually, we will want to have specific syntax
        # that allows for selecting all asset keys for a given multi-asset
        # https://github.com/dagster-io/dagster/issues/6647.
        for op_name, asset_key_set in op_names_to_asset_keys.items():
            are_keys_in_set = [key in seen_asset_keys for key in asset_key_set]
            if any(are_keys_in_set) and not all(are_keys_in_set):
                raise DagsterInvalidDefinitionError(
                    f"When building job '{job_name}', the asset '{op_name}' "
                    f"contains asset keys {sorted(list(asset_key_set))}, but "
                    f"attempted to select only {sorted(list(asset_key_set.intersection(seen_asset_keys)))}. "
                    "Selecting only some of the asset keys for a particular "
                    "asset is not yet supported behavior. Please select all "
                    "asset keys produced by a given asset when subsetting."
                )
        return op_selection

    @staticmethod
    def from_package_module(
        package_module: ModuleType,
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
        executor_def: Optional[ExecutorDefinition] = None,
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

        Returns:
            AssetGroup: An asset group with all the assets in the package.
        """
        return AssetGroup.from_modules(
            _find_modules_in_package(package_module),
            resource_defs=resource_defs,
            executor_def=executor_def,
        )

    @staticmethod
    def from_package_name(
        package_name: str,
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
        executor_def: Optional[ExecutorDefinition] = None,
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

        Returns:
            AssetGroup: An asset group with all the assets in the package.
        """
        package_module = import_module(package_name)
        return AssetGroup.from_package_module(
            package_module, resource_defs=resource_defs, executor_def=executor_def
        )

    @staticmethod
    def from_modules(
        modules: Iterable[ModuleType],
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
        executor_def: Optional[ExecutorDefinition] = None,
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

        Returns:
            AssetGroup: An asset group with all the assets defined in the given modules.
        """
        asset_ids: Set[int] = set()
        asset_keys: Dict[AssetKey, ModuleType] = dict()
        source_assets: List[SourceAsset] = []
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
    ) -> "AssetGroup":
        """
        Constructs an AssetGroup that includes all asset definitions and source assets in the module
        where this is called from.

        Args:
            resource_defs (Optional[Mapping[str, ResourceDefinition]]): A dictionary of resource
                definitions to include on the returned asset group.
            executor_def (Optional[ExecutorDefinition]): An executor to include on the returned
                asset group.

        Returns:
            AssetGroup: An asset group with all the assets defined in the module.
        """
        caller = inspect.stack()[1]
        module = inspect.getmodule(caller[0])
        if module is None:
            check.failed("Could not find a module for the caller")
        return AssetGroup.from_modules([module], resource_defs, executor_def)

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


from dagster.core.definitions.executor_definition import in_process_executor
from dagster.core.errors import DagsterUnmetExecutorRequirementsError


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
            f"Tried find modules in package {package_module}, but its __file__ is None"
        )


def _validate_resource_reqs_for_asset_group(
    asset_list: Sequence[AssetsDefinition],
    source_assets: Sequence[SourceAsset],
    resource_defs: Mapping[str, ResourceDefinition],
):
    present_resource_keys = set(resource_defs.keys())
    for asset_def in asset_list:
        resource_keys = set(asset_def.op.required_resource_keys or {})
        missing_resource_keys = list(set(resource_keys) - present_resource_keys)
        if missing_resource_keys:
            raise DagsterInvalidDefinitionError(
                f"AssetGroup is missing required resource keys for asset '{asset_def.op.name}'. Missing resource keys: {missing_resource_keys}"
            )

        for asset_key, output_def in asset_def.output_defs_by_asset_key.items():
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
