import datetime

from dagster import (
    AssetMaterialization,
    AssetSpec,
    Definitions,
    SensorEvaluationContext,
    SensorResult,
    external_asset_from_spec,
    sensor,
)


def utc_now_str() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d, %H:%M:%S")


@sensor()
def keep_external_asset_a_up_to_date(context: SensorEvaluationContext) -> SensorResult:
    # Materialization happened in external system, but is recorded here
    return SensorResult(
        asset_events=[
            AssetMaterialization(
                asset_key="external_asset_a",
                metadata={
                    "source": f'From sensor "{context.sensor_name}" at UTC time "{utc_now_str()}"'
                },
            )
        ]
    )


defs = Definitions(
    assets=[external_asset_from_spec(AssetSpec("external_asset_a"))],
    sensors=[keep_external_asset_a_up_to_date],
)
