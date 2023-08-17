from typing import Mapping, NamedTuple, Optional

import dagster._check as check
from dagster._core.definitions.events import AssetKey, MetadataValue
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
    def __new__(cls, asset_key: AssetKey, check_name: str):
        return super(AssetCheckEvaluationPlanned, cls).__new__(
            cls,
            asset_key=check.inst_param(asset_key, "asset_key", AssetKey),
            check_name=check.str_param(check_name, "check_name"),
        )


@whitelist_for_serdes
class AssetCheckEvaluationTargetMaterialization(
    NamedTuple(
        "_AssetCheckEvaluationTargetMaterialization",
        [
            ("storage_id", int),
            ("run_id", str),
            ("timestamp", float),
        ],
    )
):
    def __new__(cls, storage_id: int, run_id: str, timestamp: float):
        return super(AssetCheckEvaluationTargetMaterialization, cls).__new__(
            cls,
            storage_id=check.int_param(storage_id, "storage_id"),
            run_id=check.str_param(run_id, "run_id"),
            timestamp=check.float_param(timestamp, "timestamp"),
        )


@whitelist_for_serdes
class AssetCheckEvaluation(
    NamedTuple(
        "_AssetCheckEvaluation",
        [
            ("asset_key", AssetKey),
            ("check_name", str),
            ("success", bool),
            ("metadata", Mapping[str, MetadataValue]),
            ("target_materialization", Optional[AssetCheckEvaluationTargetMaterialization]),
        ],
    )
):
    def __new__(
        cls,
        asset_key: AssetKey,
        check_name: str,
        success: bool,
        metadata: Mapping[str, MetadataValue],
        target_materialization: Optional[AssetCheckEvaluationTargetMaterialization] = None,
    ):
        return super(AssetCheckEvaluation, cls).__new__(
            cls,
            asset_key=check.inst_param(asset_key, "asset_key", AssetKey),
            check_name=check.str_param(check_name, "check_name"),
            success=check.bool_param(success, "success"),
            metadata=check.dict_param(metadata, "metadata", key_type=str),
            target_materialization=check.opt_inst_param(
                target_materialization,
                "target_materialization",
                AssetCheckEvaluationTargetMaterialization,
            ),
        )
