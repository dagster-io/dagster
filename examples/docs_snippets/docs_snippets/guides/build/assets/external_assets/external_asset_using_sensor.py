import datetime

import dagster as dg


def utc_now_str() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d, %H:%M:%S")


@dg.sensor()
def keep_external_asset_a_up_to_date(
    context: dg.SensorEvaluationContext,
) -> dg.SensorResult:
    # Materialization happened in external system, but is recorded here
    return dg.SensorResult(
        asset_events=[
            dg.AssetMaterialization(
                asset_key="external_asset_a",
                metadata={
                    "source": f'From dg.sensor "{context.sensor_name}" at UTC time "{utc_now_str()}"'
                },
            )
        ]
    )


defs = dg.Definitions(
    assets=[dg.AssetSpec("external_asset_a")],
    sensors=[keep_external_asset_a_up_to_date],
)
