from typing import Mapping, NamedTuple, Optional

import dagster._check as check
from dagster._annotations import PublicAttr, experimental
from dagster._core.definitions.events import AssetKey, MetadataValue, RawMetadataValue
from dagster._serdes import whitelist_for_serdes

from .metadata import normalize_metadata


@experimental
@whitelist_for_serdes
class AssetCheckResult(
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
    """The result of an asset check.

    Attributes:
        asset_key (AssetKey):
            The asset key that was checked.
        check_name (str):
            The name of the check.
        success (bool):
            The pass/fail result of the check.
        metadata (Optional[Dict[str, RawMetadataValue]]):
            Arbitrary metadata about the asset.  Keys are displayed string labels, and values are
            one of the following: string, float, int, JSON-serializable dict, JSON-serializable
            list, and one of the data classes returned by a MetadataValue static method.
    """

    def __new__(
        cls,
        asset_key: AssetKey,
        check_name: str,
        success: bool,
        metadata: Optional[Mapping[str, RawMetadataValue]] = None,
    ):
        normalized_metadata = normalize_metadata(
            check.opt_mapping_param(metadata, "metadata", key_type=str),
        )
        return super().__new__(
            cls,
            asset_key=check.inst_param(asset_key, "asset_key", AssetKey),
            check_name=check.str_param(check_name, "check_name"),
            success=check.bool_param(success, "success"),
            metadata=normalized_metadata,
        )
