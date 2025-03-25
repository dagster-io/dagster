from collections.abc import Mapping
from typing import TYPE_CHECKING, AbstractSet, NamedTuple, Optional  # noqa: UP035

import dagster._check as check
from dagster._annotations import PublicAttr
from dagster._core.definitions.asset_check_evaluation import (
    AssetCheckEvaluation,
    AssetCheckEvaluationTargetMaterializationData,
)
from dagster._core.definitions.asset_check_spec import AssetCheckKey, AssetCheckSeverity
from dagster._core.definitions.events import (
    AssetKey,
    CoercibleToAssetKey,
    EventWithMetadata,
    MetadataValue,
    RawMetadataValue,
    normalize_metadata,
)
from dagster._core.errors import DagsterInvariantViolationError

if TYPE_CHECKING:
    from dagster._core.execution.context.compute import StepExecutionContext


class AssetCheckResult(
    NamedTuple(
        "_AssetCheckResult",
        [
            ("passed", PublicAttr[bool]),
            ("asset_key", PublicAttr[Optional[AssetKey]]),
            ("check_name", PublicAttr[Optional[str]]),
            ("metadata", PublicAttr[Mapping[str, MetadataValue]]),
            ("severity", PublicAttr[AssetCheckSeverity]),
            ("description", PublicAttr[Optional[str]]),
        ],
    ),
    EventWithMetadata,
):
    """The result of an asset check.

    Args:
        asset_key (Optional[AssetKey]):
            The asset key that was checked.
        check_name (Optional[str]):
            The name of the check.
        passed (bool):
            The pass/fail result of the check.
        metadata (Optional[Dict[str, RawMetadataValue]]):
            Arbitrary metadata about the asset.  Keys are displayed string labels, and values are
            one of the following: string, float, int, JSON-serializable dict, JSON-serializable
            list, and one of the data classes returned by a MetadataValue static method.
        severity (AssetCheckSeverity):
            Severity of the check. Defaults to ERROR.
        description (Optional[str]):
            A text description of the result of the check evaluation.
    """

    def __new__(
        cls,
        *,
        passed: bool,
        asset_key: Optional[CoercibleToAssetKey] = None,
        check_name: Optional[str] = None,
        metadata: Optional[Mapping[str, RawMetadataValue]] = None,
        severity: AssetCheckSeverity = AssetCheckSeverity.ERROR,
        description: Optional[str] = None,
    ):
        normalized_metadata = normalize_metadata(
            check.opt_mapping_param(metadata, "metadata", key_type=str),
        )
        return super().__new__(
            cls,
            asset_key=AssetKey.from_coercible(asset_key) if asset_key is not None else None,
            check_name=check.opt_str_param(check_name, "check_name"),
            passed=check.bool_param(passed, "passed"),
            metadata=normalized_metadata,
            severity=check.inst_param(severity, "severity", AssetCheckSeverity),
            description=check.opt_str_param(description, "description"),
        )

    def resolve_target_check_key(
        self, check_names_by_asset_key: Optional[Mapping[AssetKey, AbstractSet[str]]]
    ) -> AssetCheckKey:
        if not check_names_by_asset_key:
            raise DagsterInvariantViolationError(
                "Received unexpected AssetCheckResult. No AssetCheckSpecs were found for this step."
                "You may need to set `check_specs` on the asset decorator, or you may be emitting an "
                "AssetCheckResult that isn't in the subset passed in `context.selected_asset_check_keys`."
            )

        asset_keys_with_specs = check_names_by_asset_key.keys()

        if self.asset_key is not None:
            if self.asset_key not in asset_keys_with_specs:
                raise DagsterInvariantViolationError(
                    "Received unexpected AssetCheckResult. It targets asset"
                    f" '{self.asset_key.to_user_string()}' which is not targeted by any of the"
                    " checks currently being evaluated. Targeted assets:"
                    f" {[asset_key.to_user_string() for asset_key in asset_keys_with_specs]}."
                )

            resolved_asset_key = self.asset_key

        else:
            if len(check_names_by_asset_key) > 1:
                raise DagsterInvariantViolationError(
                    "AssetCheckResult didn't specify an asset key, but there are multiple assets"
                    " to choose from:"
                    f" {[asset_key.to_user_string() for asset_key in check_names_by_asset_key.keys()]}"
                )

            resolved_asset_key = next(iter(asset_keys_with_specs))

        check_names_with_specs = check_names_by_asset_key[resolved_asset_key]
        if self.check_name is not None:
            if self.check_name not in check_names_with_specs:
                raise DagsterInvariantViolationError(
                    "Received unexpected AssetCheckResult. No checks currently being evaluated"
                    f" target asset '{resolved_asset_key.to_user_string()}' and have name"
                    f" '{self.check_name}'. Checks being evaluated for this asset:"
                    f" {check_names_with_specs}"
                )

            resolved_check_name = self.check_name
        else:
            if len(check_names_with_specs) > 1:
                raise DagsterInvariantViolationError(
                    "AssetCheckResult result didn't specify a check name, but there are multiple"
                    " checks to choose from for the this asset key:"
                    f" {check_names_with_specs}"
                )

            resolved_check_name = next(iter(check_names_with_specs))

        return AssetCheckKey(asset_key=resolved_asset_key, name=resolved_check_name)

    def to_asset_check_evaluation(
        self, step_context: "StepExecutionContext"
    ) -> AssetCheckEvaluation:
        check_names_by_asset_key = (
            step_context.job_def.asset_layer.check_names_by_asset_key_by_node_handle.get(
                step_context.node_handle.root
            )
        )

        check_key = self.resolve_target_check_key(check_names_by_asset_key)

        input_asset_info = step_context.maybe_fetch_and_get_input_asset_version_info(
            check_key.asset_key
        )
        from dagster._core.events import DagsterEventType

        if (
            input_asset_info is not None
            and input_asset_info.event_type == DagsterEventType.ASSET_MATERIALIZATION
        ):
            target_materialization_data = AssetCheckEvaluationTargetMaterializationData(
                run_id=input_asset_info.run_id,
                storage_id=input_asset_info.storage_id,
                timestamp=input_asset_info.timestamp,
            )
        else:
            target_materialization_data = None

        return AssetCheckEvaluation(
            check_name=check_key.name,
            asset_key=check_key.asset_key,
            passed=self.passed,
            metadata=self.metadata,
            target_materialization_data=target_materialization_data,
            severity=self.severity,
            description=self.description,
        )

    def with_metadata(self, metadata: Mapping[str, RawMetadataValue]) -> "AssetCheckResult":  # pyright: ignore[reportIncompatibleMethodOverride]
        return AssetCheckResult(
            passed=self.passed,
            asset_key=self.asset_key,
            check_name=self.check_name,
            metadata=metadata,
            severity=self.severity,
            description=self.description,
        )
