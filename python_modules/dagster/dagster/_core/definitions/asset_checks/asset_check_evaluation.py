from collections.abc import Mapping
from typing import NamedTuple, Optional

import dagster._check as check
from dagster._core.definitions.asset_checks.asset_check_spec import (
    AssetCheckKey,
    AssetCheckSeverity,
)
from dagster._core.definitions.events import AssetKey, MetadataValue, RawMetadataValue
from dagster._core.definitions.metadata import normalize_metadata
from dagster._serdes import whitelist_for_serdes


@whitelist_for_serdes
class AssetCheckEvaluationPlanned(
    NamedTuple(
        "_AssetCheckEvaluationPlanned",
        [
            ("asset_key", AssetKey),
            ("check_name", str),
        ],
    )
):
    """Metadata for the event when an asset check is launched."""

    def __new__(cls, asset_key: AssetKey, check_name: str):
        return super().__new__(
            cls,
            asset_key=check.inst_param(asset_key, "asset_key", AssetKey),
            check_name=check.str_param(check_name, "check_name"),
        )

    @property
    def asset_check_key(self) -> AssetCheckKey:
        return AssetCheckKey(self.asset_key, self.check_name)


@whitelist_for_serdes
class AssetCheckEvaluationTargetMaterializationData(
    NamedTuple(
        "_AssetCheckEvaluationTargetMaterializationData",
        [
            ("storage_id", int),
            ("run_id", str),
            ("timestamp", float),
        ],
    )
):
    """A pointer to the latest materialization at execution time of an asset check."""

    def __new__(cls, storage_id: int, run_id: str, timestamp: float):
        return super().__new__(
            cls,
            storage_id=check.int_param(storage_id, "storage_id"),
            run_id=check.str_param(run_id, "run_id"),
            timestamp=check.float_param(timestamp, "timestamp"),
        )


@whitelist_for_serdes(storage_field_names={"passed": "success"})
class AssetCheckEvaluation(
    NamedTuple(
        "_AssetCheckEvaluation",
        [
            ("asset_key", AssetKey),
            ("check_name", str),
            ("passed", bool),
            ("metadata", Mapping[str, MetadataValue]),
            (
                "target_materialization_data",
                Optional[AssetCheckEvaluationTargetMaterializationData],
            ),
            ("severity", AssetCheckSeverity),
            ("description", Optional[str]),
            ("blocking", Optional[bool]),
        ],
    )
):
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
    """

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
    ):
        normed_metadata = normalize_metadata(
            check.opt_mapping_param(metadata, "metadata", key_type=str),
        )

        return super().__new__(
            cls,
            asset_key=check.inst_param(asset_key, "asset_key", AssetKey),
            check_name=check.str_param(check_name, "check_name"),
            passed=check.bool_param(passed, "passed"),
            metadata=normed_metadata,
            target_materialization_data=check.opt_inst_param(
                target_materialization_data,
                "target_materialization_data",
                AssetCheckEvaluationTargetMaterializationData,
            ),
            severity=check.inst_param(severity, "severity", AssetCheckSeverity),
            description=check.opt_str_param(description, "description"),
            blocking=check.opt_bool_param(blocking, "blocking"),
        )

    @property
    def asset_check_key(self) -> AssetCheckKey:
        return AssetCheckKey(self.asset_key, self.check_name)

    def with_metadata(self, metadata: Mapping[str, RawMetadataValue]) -> "AssetCheckEvaluation":
        normed_metadata = normalize_metadata(
            check.opt_mapping_param(metadata, "metadata", key_type=str),
        )
        return self._replace(metadata=normed_metadata)
