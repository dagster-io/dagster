import dagster as dg

# A location with an explicit automation condition sensor covering every asset, plus a
# conditioned job. The job key is claimed by the default automation condition sensor.
# With two sensors present, the job must be evaluated by exactly one of them.


@dg.asset
def covered_asset() -> None: ...


my_job = dg.define_asset_job(
    "my_job",
    selection=[covered_asset],
    automation_condition=dg.AutomationCondition.all_job_root_assets_match(
        dg.AutomationCondition.missing()
    ),
)

defs = dg.Definitions(
    assets=[covered_asset],
    jobs=[my_job],
    sensors=[dg.AutomationConditionSensorDefinition("explicit_sensor", target="*")],
)
