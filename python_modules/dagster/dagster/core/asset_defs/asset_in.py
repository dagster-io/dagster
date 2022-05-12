from typing import Any, Mapping, NamedTuple, Optional, Sequence

import dagster._check as check
from dagster.core.definitions.events import AssetKey


class AssetIn(
    NamedTuple(
        "_AssetIn",
        [
            ("asset_key", Optional[AssetKey]),
            ("metadata", Optional[Mapping[str, Any]]),
            ("namespace", Optional[Sequence[str]]),
        ],
    )
):
    def __new__(
        cls,
        asset_key: Optional[AssetKey] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        namespace: Optional[Sequence[str]] = None,
    ):
        check.invariant(
            not (asset_key and namespace),
            ("Asset key and namespace cannot both be set on AssetIn"),
        )

        # if user inputs a single string, coerce to list
        namespace = [namespace] if isinstance(namespace, str) else namespace

        return super(AssetIn, cls).__new__(
            cls,
            asset_key=check.opt_inst_param(asset_key, "asset_key", AssetKey),
            metadata=check.opt_inst_param(metadata, "metadata", Mapping),
            namespace=check.opt_list_param(namespace, "namespace", str),
        )
