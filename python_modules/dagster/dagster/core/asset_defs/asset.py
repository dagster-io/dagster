import copy
from typing import AbstractSet, Mapping, Optional

from dagster import check
from dagster.core.definitions import OpDefinition
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.partition import PartitionsDefinition

from .partition_mapping import PartitionMapping


class AssetsDefinition:
    def __init__(
        self,
        input_names_by_asset_key: Mapping[AssetKey, str],
        output_names_by_asset_key: Mapping[AssetKey, str],
        op: OpDefinition,
        partitions_def: Optional[PartitionsDefinition] = None,
        partition_mappings: Optional[Mapping[AssetKey, PartitionMapping]] = None,
        can_subset: bool = False,
    ):
        self._op = op
        self._input_defs_by_asset_key = {
            asset_key: op.input_dict[input_name]
            for asset_key, input_name in input_names_by_asset_key.items()
        }

        self._output_defs_by_asset_key = {
            asset_key: op.output_dict[output_name]
            for asset_key, output_name in output_names_by_asset_key.items()
        }
        self._partitions_def = partitions_def
        self._partition_mappings = partition_mappings or {}
        self._can_subset = can_subset

    @property
    def can_subset(self) -> bool:
        return self._can_subset

    def __call__(self, *args, **kwargs):
        return self._op(*args, **kwargs)

    @property
    def op(self) -> OpDefinition:
        return self._op

    @property
    def asset_keys(self) -> AbstractSet[AssetKey]:
        return self._output_defs_by_asset_key.keys()

    @property
    def output_defs_by_asset_key(self):
        return self._output_defs_by_asset_key

    @property
    def input_defs_by_asset_key(self):
        return self._input_defs_by_asset_key

    @property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        return self._partitions_def

    def subset_for(self, all_asset_keys: AbstractSet[AssetKey]) -> "AssetsDefinition":
        """
        Create a subset of this multi-asset that will only materialize the assets in the input set,
        and whose operation will also only depend on the assets in the input set.
        """
        if not self.can_subset:
            raise "TODO: can't subset but tried to"
        # asset keys that the operation will be expected to produce
        required_output_asset_keys = all_asset_keys.intersection(self.asset_keys)
        if not required_output_asset_keys:
            raise "TODO: no assets in this set are required, so why subset?"
        required_input_asset_keys = all_asset_keys.intersection(self.input_defs_by_asset_key.keys())

        # can't have different ops with the same name, so create a deterministic way of generating
        # a new name from the asset keys
        name_modifier = hex(
            int(
                "".join(
                    (
                        "1" if ak in required_output_asset_keys else "0"
                        for ak in sorted(self.asset_keys)
                    )
                ),
                2,
            )
        )
        # create a new op to carry out this modified operation
        new_op = OpDefinition(
            name=self.op.name + name_modifier,
            input_defs=[self.input_defs_by_asset_key[ak] for ak in required_input_asset_keys],
            output_defs=[self.output_defs_by_asset_key[ak] for ak in required_output_asset_keys],
            compute_fn=self.op.compute_fn,
            config_schema=self.op.config_schema,
            description=self.op.description,
            tags=self.op.tags,
            required_resource_keys=self.op.required_resource_keys,
            version=self.op.version,
            retry_policy=self.op.retry_policy,
        )

        return AssetsDefinition(
            {ak: self.input_defs_by_asset_key[ak].name for ak in required_input_asset_keys},
            {ak: self.output_defs_by_asset_key[ak].name for ak in required_output_asset_keys},
            new_op,
            self.partitions_def,
            self._partition_mappings,
            self.can_subset,
        )

    def get_partition_mapping(self, in_asset_key: AssetKey) -> PartitionMapping:
        if self._partitions_def is None:
            check.failed("Asset is not partitioned")

        return self._partition_mappings.get(
            in_asset_key,
            self._partitions_def.get_default_partition_mapping(),
        )
