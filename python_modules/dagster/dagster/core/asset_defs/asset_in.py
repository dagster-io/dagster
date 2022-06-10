from typing import Any, Mapping, NamedTuple, Optional, Sequence, Union

import dagster._check as check
from dagster.core.definitions.events import (
    ASSET_KEY_DELIMITER,
    AssetKey,
    CoercibleToAssetKey,
    CoercibleToAssetKeyPrefix,
)
from dagster.utils.backcompat import canonicalize_backcompat_args


class AssetIn(
    NamedTuple(
        "_AssetIn",
        [
            ("asset_key", Optional[AssetKey]),
            ("metadata", Optional[Mapping[str, Any]]),
            ("key_prefix", Optional[Sequence[str]]),
        ],
    )
):
    def __new__(
        cls,
        asset_key: Optional[CoercibleToAssetKey] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        namespace: Optional[Sequence[str]] = None,
        key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    ):
        key_prefix = canonicalize_backcompat_args(
            key_prefix, "key_prefix", namespace, "namespace", "0.16.0"
        )
        if isinstance(key_prefix, str):
            key_prefix = [key_prefix]

        check.invariant(
            not (asset_key and key_prefix),
            ("Asset key and key_prefix cannot both be set on AssetIn"),
        )

        return super(AssetIn, cls).__new__(
            cls,
            asset_key=AssetKey.from_coerceable(asset_key) if asset_key is not None else None,
            metadata=check.opt_inst_param(metadata, "metadata", Mapping),
            key_prefix=check.opt_list_param(key_prefix, "key_prefix", of_type=str),
        )
