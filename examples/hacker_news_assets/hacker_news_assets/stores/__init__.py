from dagster import AssetStore

s3_object_store = AssetStore(name="s3", io_manager_key="io_manager")
snowflake_store = AssetStore(name="snowflake", io_manager_key="warehouse_io_manager")
