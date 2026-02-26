from collections.abc import Mapping
from typing import Any

from dagster._core.definitions.asset_key import AssetKey
from dagster._record import record
from dagster._utils.merger import merge_dicts


@record
class OutputMetadataHandle:
    output_name: str
    mapping_key: str | None


@record
class AssetMetadataHandle:
    asset_key: AssetKey
    partition_key: str | None


@record
class OutputMetadataAccumulator:
    per_output_metadata: Mapping[OutputMetadataHandle | AssetMetadataHandle, Mapping[str, Any]]

    @staticmethod
    def empty() -> "OutputMetadataAccumulator":
        return OutputMetadataAccumulator(per_output_metadata={})

    def get_output_metadata(self, output_name: str, mapping_key: str | None) -> Mapping[str, Any]:
        handle = OutputMetadataHandle(
            output_name=output_name,
            mapping_key=mapping_key,
        )
        return self.per_output_metadata.get(handle, {})

    def get_asset_metadata(
        self, asset_key: AssetKey, partition_key: str | None
    ) -> Mapping[str, Any]:
        handle = AssetMetadataHandle(
            asset_key=asset_key,
            partition_key=partition_key,
        )
        return self.per_output_metadata.get(handle, {})

    def with_additional_output_metadata(
        self,
        output_name: str,
        mapping_key: str | None,
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
        self, handle: OutputMetadataHandle | AssetMetadataHandle, metadata: Mapping[str, Any]
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
        partition_key: str | None,
        metadata: Mapping[str, Any],
    ) -> "OutputMetadataAccumulator":
        return self._with_metadata(
            handle=AssetMetadataHandle(
                asset_key=asset_key,
                partition_key=partition_key,
            ),
            metadata=metadata,
        )
