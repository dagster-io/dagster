import dagster as dg

downstream_job = dg.define_asset_job("downstream_job", selection=["downstream"])


@dg.asset_sensor(asset_key=dg.AssetKey("raw_data"), job=downstream_job)
def raw_data_sensor(context: dg.SensorEvaluationContext, asset_event: dg.EventLogEntry):
    return dg.RunRequest()
