from dagster import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.external_asset import (
    external_assets_from_specs,
)

external_asset_defs = external_assets_from_specs(
    specs=[
        AssetSpec(
            key=AssetKey(["s3", "iot_raw_telem_eu"]),
            group_name="external_assets",
        ),
        AssetSpec(
            key=AssetKey(["s3", "iot_scrubbed_telem_eu"]),
            deps=[AssetKey(["s3", "iot_raw_telem_eu"])],
            group_name="external_assets",
        ),
        AssetSpec(
            key=AssetKey(["s3", "iot_raw_telem_americas"]),
            group_name="external_assets",
        ),
        AssetSpec(
            key=AssetKey(["s3", "iot_scrubbed_telem_americas"]),
            deps=[AssetKey(["s3", "iot_raw_telem_americas"])],
            group_name="external_assets",
        ),
        AssetSpec(
            key=AssetKey(["s3", "iot_raw_telem_apac"]),
            group_name="external_assets",
        ),
        AssetSpec(
            key=AssetKey(["s3", "iot_scrubbed_telem_apac"]),
            deps=[AssetKey(["s3", "iot_raw_telem_apac"])],
            group_name="external_assets",
        ),
        AssetSpec(
            key=AssetKey(["vendors", "telem_vendor_foo"]),
            group_name="external_assets",
        ),
        AssetSpec(
            key=AssetKey(["vendors", "telem_vendor_bar"]),
            group_name="external_assets",
        ),
        AssetSpec(
            key=AssetKey(["s3", "joined_sensor_telem"]),
            deps=[
                AssetKey(["vendors", "telem_vendor_foo"]),
                AssetKey(["vendors", "telem_vendor_bar"]),
                AssetKey(["s3", "iot_scrubbed_telem_apac"]),
                AssetKey(["s3", "iot_scrubbed_telem_americas"]),
                AssetKey(["s3", "iot_scrubbed_telem_eu"]),
            ],
            group_name="external_assets",
        ),
        AssetSpec(
            key=AssetKey(["static", "admin_boundaries"]),
            group_name="external_assets",
        ),
    ]
)
