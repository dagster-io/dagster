import itertools
from functools import cached_property
from typing import AbstractSet, Dict, Mapping, Optional

import dagster._check as check
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey, AssetKeyOrCheckKey
from dagster._core.definitions.asset_spec import AssetExecutionType
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.dependency import NodeOutputHandle
from dagster._core.definitions.graph_definition import SubselectedGraphDefinition
from dagster._record import IHaveNew, record_custom

from .node_definition import NodeDefinition


@record_custom
class AssetGraphComputation(IHaveNew):
    """A computation whose purpose is to materialize assets, observe assets, and/or evaluate asset
    checks.

    Binds a NodeDefinition to the asset keys and asset check keys that it interacts with.
    """

    node_def: NodeDefinition
    keys_by_input_name: Mapping[str, AssetKey]
    keys_by_output_name: Mapping[str, AssetKey]
    check_keys_by_output_name: Mapping[str, AssetCheckKey]
    backfill_policy: Optional[BackfillPolicy]
    can_subset: bool
    is_subset: bool
    selected_asset_keys: AbstractSet[AssetKey]
    selected_asset_check_keys: AbstractSet[AssetCheckKey]
    output_names_by_key: Mapping[AssetKey, str]
    execution_type: AssetExecutionType

    def __new__(
        cls,
        node_def: NodeDefinition,
        keys_by_input_name: Mapping[str, AssetKey],
        keys_by_output_name: Mapping[str, AssetKey],
        check_keys_by_output_name: Mapping[str, AssetCheckKey],
        backfill_policy: Optional[BackfillPolicy],
        can_subset: bool,
        is_subset: bool,
        selected_asset_keys: AbstractSet[AssetKey],
        selected_asset_check_keys: AbstractSet[AssetCheckKey],
        execution_type: AssetExecutionType,
    ):
        output_names_by_key: Dict[AssetKey, str] = {}
        for output_name, key in keys_by_output_name.items():
            if key in output_names_by_key:
                check.failed(
                    f"Outputs '{output_names_by_key[key]}' and '{output_name}' both target the "
                    "same asset key. Each asset key should correspond to a single output."
                )
            output_names_by_key[key] = output_name

        return super().__new__(
            cls,
            node_def=node_def,
            keys_by_input_name=keys_by_input_name,
            keys_by_output_name=keys_by_output_name,
            check_keys_by_output_name=check_keys_by_output_name,
            backfill_policy=backfill_policy,
            can_subset=can_subset,
            is_subset=is_subset,
            selected_asset_keys=selected_asset_keys,
            selected_asset_check_keys=selected_asset_check_keys,
            output_names_by_key=output_names_by_key,
            execution_type=execution_type,
        )

    @cached_property
    def asset_or_check_keys_by_op_output_handle(
        self,
    ) -> Mapping[NodeOutputHandle, AssetKeyOrCheckKey]:
        result = {}
        for output_name, key in itertools.chain(
            self.keys_by_output_name.items(), self.check_keys_by_output_name.items()
        ):
            output_def, node_handle = self.full_node_def.resolve_output_to_origin(output_name, None)
            result[NodeOutputHandle(node_handle=node_handle, output_name=output_def.name)] = key

        return result

    @property
    def full_node_def(self) -> NodeDefinition:
        node_def = self.node_def
        while isinstance(node_def, SubselectedGraphDefinition):
            node_def = node_def.parent_graph_def

        return node_def
