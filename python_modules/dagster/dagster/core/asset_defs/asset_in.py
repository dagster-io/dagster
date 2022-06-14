from typing import Any, Mapping, NamedTuple, Optional, Sequence

import dagster._check as check
from dagster.core.definitions.events import AssetKey, CoercibleToAssetKey, CoercibleToAssetKeyPrefix
from dagster.utils.backcompat import canonicalize_backcompat_args


class AssetIn(
    NamedTuple(
        "_AssetIn",
        [
            ("key", Optional[AssetKey]),
            ("metadata", Optional[Mapping[str, Any]]),
            ("key_prefix", Optional[Sequence[str]]),
        ],
    )
):
    """
    Defines an asset dependency.

    Attributes:
        key_prefix (Optional[Union[str, Sequence[str]]]): If provided, the asset's key is the
            concatenation of the key_prefix and the input name. Only one of the "key_prefix" and
            "key" arguments should be provided.
        key (Optional[Union[str, Sequence[str], AssetKey]]): The asset's key. Only one of the
            "key_prefix" and "key" arguments should be provided.
        metadata (Optional[Dict[str, Any]]): A dict of the metadata for the input.
            For example, if you only need a subset of columns from an upstream table, you could
            include that in metadata and the IO manager that loads the upstream table could use the
            metadata to determine which columns to load.
    """

    def __new__(
        cls,
        key: Optional[CoercibleToAssetKey] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        namespace: Optional[Sequence[str]] = None,
        key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
        asset_key: Optional[CoercibleToAssetKey] = None,
    ):
        key_prefix = canonicalize_backcompat_args(
            key_prefix, "key_prefix", namespace, "namespace", "0.16.0"
        )
        key = canonicalize_backcompat_args(key, "key", asset_key, "asset_key", "0.16.0")
        if isinstance(key_prefix, str):
            key_prefix = [key_prefix]

        check.invariant(
            not (key and key_prefix), "key and key_prefix cannot both be set on AssetIn"
        )

        return super(AssetIn, cls).__new__(
            cls,
            key=AssetKey.from_coerceable(key) if key is not None else None,
            metadata=check.opt_inst_param(metadata, "metadata", Mapping),
            key_prefix=check.opt_list_param(key_prefix, "key_prefix", of_type=str),
        )
