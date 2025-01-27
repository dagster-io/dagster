from collections.abc import Mapping
from typing import Any, Optional, Union

from dagster._core.definitions.asset_key import AssetKey
from dagster._record import record
from dagster._utils.merger import merge_dicts


@record
class OutputMetadataHandle:
    output_name: str
    mapping_key: Optional[str]


@record
class AssetMetadataHandle:
    asset_key: AssetKey
    partition_key: Optional[str]


@record
class OutputMetadataAccumulator:
    per_output_metadata: Mapping[
        Union[OutputMetadataHandle, AssetMetadataHandle], Mapping[str, Any]
    ]

    @staticmethod
    def empty() -> "OutputMetadataAccumulator":
        return OutputMetadataAccumulator(per_output_metadata={})

    def get_output_metadata(
        self, output_name: str, mapping_key: Optional[str]
    ) -> Mapping[str, Any]:
        handle = OutputMetadataHandle(
            output_name=output_name,
            mapping_key=mapping_key,
        )
        return self.per_output_metadata.get(handle, {})

    def get_asset_metadata(
        self, asset_key: AssetKey, partition_key: Optional[str]
    ) -> Mapping[str, Any]:
        handle = AssetMetadataHandle(
            asset_key=asset_key,
            partition_key=partition_key,
        )
        return self.per_output_metadata.get(handle, {})

    def with_additional_output_metadata(
        self,
        output_name: str,
        mapping_key: Optional[str],
        metadata: Mapping[str, Any],
    ) -> "OutputMetadataAccumulator":
        return self._with_metadata(
            handle=OutputMetadataHandle(
                output_name=output_name,
                mapping_key=mapping_key,
            ),
            metadata=metadata,
        )

    def _with_metadata(
        self, handle: Union[OutputMetadataHandle, AssetMetadataHandle], metadata: Mapping[str, Any]
    ) -> "OutputMetadataAccumulator":
        return OutputMetadataAccumulator(
            per_output_metadata=merge_dicts(
                self.per_output_metadata,
                {handle: merge_dicts(self.per_output_metadata.get(handle, {}), metadata)},
            )
        )

    def with_additional_asset_metadata(
        self,
        asset_key: AssetKey,
        partition_key: Optional[str],
        metadata: Mapping[str, Any],
    ) -> "OutputMetadataAccumulator":
        return self._with_metadata(
            handle=AssetMetadataHandle(
                asset_key=asset_key,
                partition_key=partition_key,
            ),
            metadata=metadata,
        )
