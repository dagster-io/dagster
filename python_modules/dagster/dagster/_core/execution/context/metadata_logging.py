from typing import Any, Mapping, Optional

from dagster._record import record
from dagster._utils.merger import merge_dicts


@record
class OutputMetadataHandle:
    output_name: str
    mapping_key: Optional[str]


@record
class OutputMetadataAccumulator:
    per_output_metadata: Mapping[OutputMetadataHandle, Mapping[str, Any]]

    @staticmethod
    def empty() -> "OutputMetadataAccumulator":
        return OutputMetadataAccumulator(per_output_metadata={})

    def get_metadata(self, output_name: str, mapping_key: Optional[str]) -> Mapping[str, Any]:
        handle = OutputMetadataHandle(output_name=output_name, mapping_key=mapping_key)
        return self.per_output_metadata.get(handle, {})

    def with_additional_metadata(
        self, output_name: str, mapping_key: Optional[str], metadata: Mapping[str, Any]
    ) -> "OutputMetadataAccumulator":
        handle = OutputMetadataHandle(output_name=output_name, mapping_key=mapping_key)
        return OutputMetadataAccumulator(
            per_output_metadata=merge_dicts(
                self.per_output_metadata,
                {handle: merge_dicts(self.per_output_metadata.get(handle, {}), metadata)},
            )
        )
