import re
from typing import Any, Dict, List, Mapping, NamedTuple, Optional, Sequence, Set, Union, cast

from dagster import check
from dagster.utils import merge_dicts

from ..definitions.executor_definition import ExecutorDefinition
from ..definitions.job_definition import JobDefinition
from ..definitions.op_definition import OpDefinition
from ..definitions.resource_definition import ResourceDefinition
from ..errors import DagsterInvalidDefinitionError
from .asset import AssetsDefinition
from .assets_job import build_assets_job, build_root_manager, build_source_assets_by_key
from .source_asset import SourceAsset


class AssetCollection(
    NamedTuple(
        "_AssetCollection",
        [
            ("assets", Sequence[AssetsDefinition]),
            ("source_assets", Sequence[SourceAsset]),
            ("resource_defs", Mapping[str, ResourceDefinition]),
            ("executor_def", Optional[ExecutorDefinition]),
        ],
    )
):
    def __new__(
        cls,
        assets: Sequence[AssetsDefinition],
        source_assets: Optional[Sequence[SourceAsset]] = None,
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
        executor_def: Optional[ExecutorDefinition] = None,
    ):
        from dagster.core.definitions.graph_definition import default_job_io_manager

        check.list_param(assets, "assets", of_type=AssetsDefinition)
        source_assets = check.opt_list_param(source_assets, "source_assets", of_type=SourceAsset)
        resource_defs = check.opt_dict_param(
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
        # In the case of collisions, merge_dicts takes values from the dictionary latest in the list, so we place the user provided resource defs after the defaults.
        resource_defs = merge_dicts(
            {"root_manager": root_manager, "io_manager": default_job_io_manager},
            resource_defs,
        )

        _validate_resource_reqs_for_asset_collection(
            asset_list=assets, source_assets=source_assets, resource_defs=resource_defs
        )

        return super(AssetCollection, cls).__new__(
            cls,
            assets=assets,
            source_assets=source_assets,
            resource_defs=resource_defs,
            executor_def=executor_def,
        )

    @property
    def all_assets_job_name(self) -> str:
        """The name of the mega-job that the provided list of assets is coerced into."""
        return "__ASSET_COLLECTION"

    def build_job(
        self,
        name: str,
        selection: Optional[Union[str, List[str]]] = None,
        executor_def: Optional[ExecutorDefinition] = None,
        tags: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
    ) -> JobDefinition:
        from dagster.core.selector.subset_selector import parse_op_selection

        check.str_param(name, "name")

        if not isinstance(selection, str):
            selection = check.opt_list_param(selection, "selection", of_type=str)
        executor_def = check.opt_inst_param(executor_def, "executor_def", ExecutorDefinition)
        description = check.opt_str_param(description, "description")

        mega_job_def = build_assets_job(
            name=name,
            assets=self.assets,
            source_assets=self.source_assets,
            resource_defs=self.resource_defs,
            executor_def=self.executor_def,
        )

        if selection:
            op_selection = self._parse_asset_selection(selection, job_name=name)
            # just mooching off of the logic here
            resolved_op_selection_dict = parse_op_selection(mega_job_def, op_selection)

            included_assets = []
            excluded_assets: List[Union[AssetsDefinition, ForeignAsset]] = list(self.source_assets)

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

        return build_assets_job(
            name=name,
            assets=included_assets,
            source_assets=excluded_assets,
            resource_defs=self.resource_defs,
            executor_def=self.executor_def,
            description=description,
            tags=tags,
        )

    def _parse_asset_selection(self, selection: Union[str, List[str]], job_name: str) -> List[str]:
        """Convert selection over asset key to selection over ops"""

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
            if isinstance(asset, ForeignAsset):
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
            # return None if query is invalid
            parts = token_matching.groups() if token_matching is not None else None
            if parts is None:
                raise DagsterInvalidDefinitionError(
                    f"When attempting to create job '{job_name}', the clause "
                    f"{clause} within the asset key selection was invalid. Please "
                    "review the selection syntax here (imagine there is a link "
                    "here to the docs)."
                )
            upstream_part, key_str, downstream_part = parts
            if key_str in source_asset_keys:
                raise DagsterInvalidDefinitionError(
                    f"When attempting to create job '{job_name}', the clause '{clause}' selects asset_key '{key_str}', which comes from a source asset. Source assets can't be materialized, and therefore can't be subsetted into a job. Please choose a subset on asset keys that are materializable - that is, included on assets within the collection. Valid assets: {list(asset_keys_to_ops.keys())}"
                )
            if key_str not in asset_keys_to_ops:
                raise DagsterInvalidDefinitionError(
                    f"When attempting to create job '{job_name}', the clause '{clause}' within the asset key selection did not match any asset keys. Present asset keys: {list(asset_keys_to_ops.keys())}"
                )

            seen_asset_keys.add(key_str)

            for op in asset_keys_to_ops[key_str]:

                op_clause = f"{upstream_part}{op.name}{downstream_part}"
                op_selection.append(op_clause)

        # Verify that for each selected asset key, the corresponding op had all asset keys selected.
        for op_name, asset_key_set in op_names_to_asset_keys.items():
            are_keys_in_set = [key in seen_asset_keys for key in asset_key_set]
            if any(are_keys_in_set) and not all(are_keys_in_set):
                raise DagsterInvalidDefinitionError(
                    f"When building job '{job_name}', the asset '{op_name}' contains asset keys {sorted(list(asset_key_set))}, but attempted to select only {sorted(list(asset_key_set.intersection(seen_asset_keys)))}. Selecting only some of the asset keys for a particular asset is not yet supported behavior. Please select all asset keys produced by a given asset when subsetting."
                )
        return op_selection


def _validate_resource_reqs_for_asset_collection(
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
                f"AssetCollection is missing required resource keys for asset '{asset_def.op.name}'. Missing resource keys: {missing_resource_keys}"
            )

        for asset_key, output_def in asset_def.output_defs_by_asset_key.items():
            if output_def.io_manager_key and output_def.io_manager_key not in present_resource_keys:
                raise DagsterInvalidDefinitionError(
                    f"Output '{output_def.name}' with AssetKey '{asset_key}' requires io manager '{output_def.io_manager_key}' but was not provided on asset collection. Provided resources: {sorted(list(present_resource_keys))}"
                )

    for source_asset in source_assets:
        if source_asset.io_manager_key and source_asset.io_manager_key not in present_resource_keys:
            raise DagsterInvalidDefinitionError(
                f"SourceAsset with key {source_asset.key} requires io manager with key '{source_asset.io_manager_key}', which was not provided on AssetCollection. Provided keys: {sorted(list(present_resource_keys))}"
            )

    for resource_key, resource_def in resource_defs.items():
        resource_keys = set(resource_def.required_resource_keys)
        missing_resource_keys = sorted(list(set(resource_keys) - present_resource_keys))
        if missing_resource_keys:
            raise DagsterInvalidDefinitionError(
                f"AssetCollection is missing required resource keys for resource '{resource_key}'. Missing resource keys: {missing_resource_keys}"
            )
