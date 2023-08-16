from collections import defaultdict
from typing import TYPE_CHECKING, Dict, Mapping, NamedTuple, Optional, Set

import dagster._check as check
from dagster._annotations import PublicAttr, experimental
from dagster._core.definitions.events import (
    AssetKey,
    MetadataValue,
    RawMetadataValue,
    normalize_metadata,
)
from dagster._core.errors import DagsterInvariantViolationError
from dagster._serdes import whitelist_for_serdes

if TYPE_CHECKING:
    from dagster._core.execution.context.compute import StepExecutionContext


@experimental
@whitelist_for_serdes
class AssetCheckEvaluation(
    NamedTuple(
        "_AssetCheckResult",
        [
            ("asset_key", PublicAttr[AssetKey]),
            ("check_name", PublicAttr[str]),
            ("success", PublicAttr[bool]),
            ("metadata", PublicAttr[Mapping[str, MetadataValue]]),
        ],
    )
):
    pass


@experimental
@whitelist_for_serdes
class AssetCheckResult(
    NamedTuple(
        "_AssetCheckResult",
        [
            ("success", PublicAttr[bool]),
            ("asset_key", PublicAttr[Optional[AssetKey]]),
            ("check_name", PublicAttr[Optional[str]]),
            ("metadata", PublicAttr[Mapping[str, MetadataValue]]),
        ],
    )
):
    """The result of an asset check.

    Attributes:
        asset_key (AssetKey): The asset key that was checked.
        check_name (str): The name of the check that was run.
        success (bool): The pass/fail result of the check.
        metadata (Dict[str, Any]): Any metadata about the check result.
    """

    def __new__(
        cls,
        *,
        success: bool,
        asset_key: Optional[AssetKey] = None,
        check_name: Optional[str] = None,
        metadata: Optional[Mapping[str, RawMetadataValue]] = None,
    ):
        return super().__new__(
            cls,
            asset_key=check.opt_inst_param(asset_key, "asset_key", AssetKey),
            check_name=check.opt_str_param(check_name, "check_name"),
            success=check.bool_param(success, "success"),
            metadata=normalize_metadata(
                check.opt_mapping_param(metadata, "metadata", key_type=str),
            ),
        )

    def to_asset_check_evaluation(
        self, step_context: "StepExecutionContext"
    ) -> AssetCheckEvaluation:
        specs = step_context.job_def.asset_layer.check_specs_for_node(step_context.node_handle)

        spec_check_names_by_asset_key: Dict[AssetKey, Set[str]] = defaultdict(set)
        for spec in specs:
            spec_check_names_by_asset_key[spec.asset_key].add(spec.name)

        if self.asset_key is not None:
            if self.asset_key not in spec_check_names_by_asset_key.keys():
                raise DagsterInvariantViolationError(
                    "TODO Check result is for an asset that is not targeted by any the checks in"
                    " the checks definition. Here the asest key and here are the assets targeted by"
                    " the checks definition."
                )

            resolved_asset_key = self.asset_key

        else:
            if len(spec_check_names_by_asset_key) > 1:
                raise DagsterInvariantViolationError(
                    "TODO Check result didn't specify an asset key, but there are multiple assets"
                    " to choose from: {name the assets}"
                )

            resolved_asset_key = next(iter(spec_check_names_by_asset_key.keys()))

        spec_check_names_for_asset_key = spec_check_names_by_asset_key[resolved_asset_key]
        if self.check_name is not None:
            if self.check_name not in spec_check_names_for_asset_key:
                raise DagsterInvariantViolationError(
                    "No check specs currently being evaluated contain check with asset X and"
                    " name Y. Checks for this asset include {}."
                )

            resolved_check_name = self.check_name
        else:
            if len(spec_check_names_for_asset_key) > 1:
                raise DagsterInvariantViolationError(
                    "TODO Check result didn't specify a check name, but there are multiple"
                    " checks to choose from for the this asset key: {name the checks}"
                )

            resolved_check_name = next(iter(spec_check_names_for_asset_key))

        return AssetCheckEvaluation(
            check_name=resolved_check_name,
            asset_key=resolved_asset_key,
            success=self.success,
            metadata=self.metadata,
            # tags=get_input_version_tags(),
        )


# def _get_version_tags_for_check(step_context: StepExecutionContext):
#     if (
#         step_context.is_external_input_asset_version_info_loaded
#         and asset_key in step_context.job_def.asset_layer.asset_keys
#     ):
#         input_provenance_data = _get_input_provenance_data(asset_key, step_context)
#         _build_data_version_tags(
#             input_provenance_data,
#             user_provided_data_version is not None,
#         )
#     else:
#         pass
