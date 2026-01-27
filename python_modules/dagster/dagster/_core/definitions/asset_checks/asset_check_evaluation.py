from collections.abc import Mapping
from typing import Optional

import dagster_shared.check as check
from dagster_shared.record import IHaveNew, record, record_custom, replace

from dagster._core.definitions.asset_checks.asset_check_spec import (
    AssetCheckKey,
    AssetCheckSeverity,
)
from dagster._core.definitions.events import AssetKey, MetadataValue, RawMetadataValue
from dagster._core.definitions.metadata import normalize_metadata
from dagster._core.definitions.partitions.subset import PartitionsSubset
from dagster._serdes import whitelist_for_serdes


@whitelist_for_serdes
@record
class AssetCheckEvaluationPlanned:
    """Metadata for the event when an asset check is launched."""

    asset_key: AssetKey
    check_name: str
    partitions_subset: Optional[PartitionsSubset] = None

    @property
    def asset_check_key(self) -> AssetCheckKey:
        return AssetCheckKey(self.asset_key, self.check_name)


@whitelist_for_serdes
@record
class AssetCheckEvaluationTargetMaterializationData:
    """A pointer to the latest materialization at execution time of an asset check."""

    storage_id: int
    run_id: str
    timestamp: float


@whitelist_for_serdes(storage_field_names={"passed": "success"})
@record_custom
class AssetCheckEvaluation(IHaveNew):
    """Represents the outcome of a evaluating an asset check.

    Args:
        asset_key (AssetKey):
            The asset key that was checked.
        check_name (str):
            The name of the check.
        passed (bool):
            The pass/fail result of the check.
        metadata (Optional[Mapping[str, MetadataValue]]):
            Arbitrary user-provided metadata about the asset.  Keys are displayed string labels, and
            values are one of the following: string, float, int, JSON-serializable dict, JSON-serializable
            list, and one of the data classes returned by a MetadataValue static method.
        target_materialization_data (Optional[AssetCheckEvaluationTargetMaterializationData]):
            The latest materialization at execution time of the check.
        severity (AssetCheckSeverity):
            Severity of the check result.
        description (Optional[str]):
            A text description of the result of the check evaluation.
        blocking (Optional[bool]):
            Whether the check is blocking.
        partition (Optional[str]):
            The partition that the check was evaluated on, if applicable.
    """

    asset_key: AssetKey
    check_name: str
    passed: bool
    metadata: Mapping[str, MetadataValue]
    target_materialization_data: Optional[AssetCheckEvaluationTargetMaterializationData]
    severity: AssetCheckSeverity
    description: Optional[str]
    blocking: Optional[bool]
    partition: Optional[str]

    def __new__(
        cls,
        asset_key: AssetKey,
        check_name: str,
        passed: bool,
        metadata: Optional[Mapping[str, RawMetadataValue]] = None,
        target_materialization_data: Optional[AssetCheckEvaluationTargetMaterializationData] = None,
        severity: AssetCheckSeverity = AssetCheckSeverity.ERROR,
        description: Optional[str] = None,
        blocking: Optional[bool] = None,
        partition: Optional[str] = None,
    ):
        return super().__new__(
            cls,
            asset_key=asset_key,
            check_name=check_name,
            passed=passed,
            metadata=normalize_metadata(
                check.opt_mapping_param(metadata, "metadata", key_type=str)
            ),
            target_materialization_data=target_materialization_data,
            severity=severity,
            description=description,
            blocking=blocking,
            partition=partition,
        )

    @property
    def asset_check_key(self) -> AssetCheckKey:
        return AssetCheckKey(self.asset_key, self.check_name)

    def with_metadata(self, metadata: Mapping[str, RawMetadataValue]) -> "AssetCheckEvaluation":
        normed_metadata = normalize_metadata(
            check.opt_mapping_param(metadata, "metadata", key_type=str),
        )
        return replace(self, metadata=normed_metadata)
