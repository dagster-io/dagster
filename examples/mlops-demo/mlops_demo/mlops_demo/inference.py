import polars as pl
import json
import pika
import dagster as dg
from sklearn.ensemble import RandomForestClassifier

group_name = "inference"

@dg.asset(
    description="Outputs the devices at risk of failure",
    group_name=group_name,
    automation_condition=dg.AutomationCondition.eager()
)
def devices_at_risk(context: dg.AssetExecutionContext, cleaned_readings: pl.DataFrame, deployed_model: RandomForestClassifier) -> list:

    feature_cols = ["Air temperature [K]", "Process temperature [K]", "Rotational speed [rpm]", "Torque [Nm]"]

    y_pred = deployed_model.predict(cleaned_readings[feature_cols])

    devices_at_risk = (
        cleaned_readings
        .select("UDI")
        .with_columns(
            pl.Series("at_risk", y_pred)
        )
        .filter(pl.col("at_risk") == 1)
        .select("UDI")
    )

    devices_at_risk_list = devices_at_risk["UDI"].to_list()

    context.add_asset_metadata({
        "devices_at_risk": devices_at_risk_list
    })

    return devices_at_risk_list