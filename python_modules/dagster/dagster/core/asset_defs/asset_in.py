from typing import Any, Mapping, NamedTuple, Optional
from dagster import check


class AssetIn(
    NamedTuple(
        "_AssetIn",
        [
            ("asset_key", Optional[str]),
            ("metadata", Optional[Mapping[str, Any]]),
            ("namespace", Optional[str]),
            ("managed", bool),
        ],
    )
):
    def __new__(
        cls,
        asset_key: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        namespace: Optional[str] = None,
        managed: bool = True,
    ):
        check.invariant(
            not (asset_key and namespace),
            ("Asset key and namespace cannot both be set on AssetIn"),
        )

        return super(AssetIn, cls).__new__(
            cls,
            asset_key=check.opt_str_param(asset_key, "asset_key"),
            metadata=check.opt_inst_param(metadata, "metadata", Mapping),
            namespace=check.opt_str_param(namespace, "namespace"),
            managed=managed,
        )
