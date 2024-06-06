from functools import cached_property
from typing import Mapping, NamedTuple, Tuple

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.input import In
from dagster._core.definitions.output import Out


class InMapping(NamedTuple):
    input_name: str
    input: In


class OutMapping(NamedTuple):
    output_name: str
    output: Out


class InOutMapper:
    def __init__(
        self,
        in_mappings: Mapping[AssetKey, InMapping],
        out_mappings: Mapping[AssetKey, OutMapping],
    ) -> None:
        self.in_mappings = in_mappings
        self.out_mappings = out_mappings

    @staticmethod
    def from_asset_ins_and_asset_outs(
        asset_ins: Mapping[AssetKey, Tuple[str, In]],
        asset_outs: Mapping[AssetKey, Tuple[str, Out]],
    ):
        in_mappings = {
            asset_key: InMapping(input_name, in_)
            for asset_key, (input_name, in_) in asset_ins.items()
        }
        out_mappings = {
            asset_key: OutMapping(output_name, out_)
            for asset_key, (output_name, out_) in asset_outs.items()
        }
        return InOutMapper(in_mappings, out_mappings)

    @cached_property
    def asset_outs_by_output_name(self) -> Mapping[str, Out]:
        return dict(self.out_mappings.values())

    @cached_property
    def keys_by_output_name(self) -> Mapping[str, AssetKey]:
        return {
            out_mapping.output_name: asset_key
            for asset_key, out_mapping in self.out_mappings.items()
        }
