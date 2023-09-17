from dagster import AssetMaterialization, DagsterInstance

from external_lib import report_asset_materialization

if __name__ == "__main__":
    report_asset_materialization(
        AssetMaterialization(
            asset_key="observable_asset_one", metadata={"foo_metadata_label": "metadata_value"}
        ),
        instance=DagsterInstance.get(),
    )
