from dagster import AssetSelection, AutoMaterializeSensorDefinition, Definitions

my_custom_auto_materialize_sensor = AutoMaterializeSensorDefinition(
    "my_custom_auto_materialize_sensor",
    asset_selection=AssetSelection.all(include_sources=True),
    minimum_interval_seconds=60 * 15,
)

defs = Definitions(sensors=[my_custom_auto_materialize_sensor])
