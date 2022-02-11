import re
from typing import List, Mapping, NamedTuple, Optional, Sequence, Union

from dagster import check
from dagster.utils import merge_dicts

from ..definitions.executor_definition import ExecutorDefinition
from ..definitions.job_definition import JobDefinition, get_subselected_graph_definition
from ..definitions.mode import ModeDefinition
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
                "Resource dictionary included resource with key 'root_manager', which is a reserved resource keyword in Dagster. Please change this key, and then change all places that require this key to a new value."
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
        asset_key_selection: Optional[Union[str, List[str]]] = None,
        executor_def: Optional[ExecutorDefinition] = None,
        description: Optional[str] = None,
    ) -> JobDefinition:
        from dagster.core.selector.subset_selector import parse_op_selection, OpSelectionData

        check.str_param(name, "name")

        if not isinstance(asset_key_selection, str):
            asset_key_selection = check.opt_list_param(
                asset_key_selection, "asset_key_selection", of_type=str
            )
        executor_def = check.opt_inst_param(executor_def, "executor_def", ExecutorDefinition)
        description = check.opt_str_param(description, "description")

        mega_job_def = build_assets_job(
            name=name,
            assets=self.assets,
            source_assets=self.source_assets,
            resource_defs=self.resource_defs,
            executor_def=self.executor_def,
        )

        orig_mode_def = mega_job_def.get_mode_definition()
        mode_def = ModeDefinition(
            resource_defs=orig_mode_def.resource_defs,
            logger_defs=orig_mode_def.loggers,
            executor_defs=[executor_def or orig_mode_def.executor_defs[0]],
        )

        if asset_key_selection:
            op_selection = self._parse_asset_selection(asset_key_selection, job_name=name)
            resolved_op_selection_dict = parse_op_selection(mega_job_def, op_selection)

            op_selection_data: Optional[OpSelectionData] = OpSelectionData(
                op_selection=op_selection,
                resolved_op_selection=set(
                    resolved_op_selection_dict.keys()
                ),  # equivalent to solids_to_execute. currently only gets top level nodes.
                parent_job_def=mega_job_def,  # used by pipeline snapshot lineage
            )

            graph = get_subselected_graph_definition(mega_job_def.graph, resolved_op_selection_dict)
        else:
            op_selection_data = None
            graph = mega_job_def.graph

        job_def = JobDefinition(
            name=name,
            description=description,
            mode_def=mode_def,
            preset_defs=mega_job_def.preset_defs,
            tags=mega_job_def.tags,
            hook_defs=mega_job_def.hook_defs,
            op_retry_policy=mega_job_def._solid_retry_policy,  # pylint: disable=protected-access
            graph_def=graph,
            version_strategy=mega_job_def.version_strategy,
            _op_selection_data=op_selection_data,
        )
        return job_def

    def _parse_asset_selection(self, asset_key_selection, job_name):
        """Convert selection over asset key to selection over ops"""

        asset_keys_to_ops = dict()

        if isinstance(asset_key_selection, str):
            asset_key_selection = [asset_key_selection]

        if len(asset_key_selection) == 1 and asset_key_selection[0] == "*":
            return asset_key_selection

        source_asset_keys = set()
        for asset in self.assets:
            # Assume that if a user subselects a source asset, that they want to re-load all inputs that may result from that source asset.
            for asset_key in asset.asset_keys:
                asset_key_as_str = ".".join([piece for piece in asset_key.path])
                if not asset_key_as_str in asset_keys_to_ops:
                    asset_keys_to_ops[asset_key_as_str] = []
                asset_keys_to_ops[asset_key_as_str].append(asset.op)

        for asset in self.source_assets:
            asset_key_as_str = ".".join([piece for piece in asset.key.path])
            source_asset_keys.add(asset_key_as_str)

        op_selection = []

        for clause in asset_key_selection:
            token_matching = re.compile(r"^(\*?\+*)?([.\w\d\[\]?_-]+)(\+*\*?)?$").search(
                clause.strip()
            )
            # return None if query is invalid
            parts = token_matching.groups() if token_matching is not None else None
            if parts is None:
                raise DagsterInvalidDefinitionError(
                    f"When attempting to create job '{job_name}', the clause {clause} within the asset key selection was invalid. Please review the selection syntax here (imagine there is a link here to the docs)."
                )
            upstream_part, asset_key, downstream_part = parts
            if asset_key in source_asset_keys:
                raise DagsterInvalidDefinitionError(
                    f"When attempting to create job '{job_name}', the clause '{clause}' selects asset_key '{asset_key}', which comes from a source asset. Source assets can't be materialized, and therefore can't be subsetted into a job. Please choose a subset on asset keys that are materializable - that is, included on assets within the collection. Valid assets: {list(asset_keys_to_ops.keys())}"
                )
            if asset_key not in asset_keys_to_ops:
                raise DagsterInvalidDefinitionError(
                    f"When attempting to create job '{job_name}', the clause '{clause}' within the asset key selection did not match any asset keys. Present asset keys: {list(asset_keys_to_ops.keys())}"
                )
            for op in asset_keys_to_ops[asset_key]:

                op_clause = f"{upstream_part}{op.name}{downstream_part}"
                op_selection.append(op_clause)
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
