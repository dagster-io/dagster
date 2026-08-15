import dagster as dg

# Conditioned entities split across an explicit sensor and the default sensor:
# - the explicit sensor covers the asset "covered" and claims "claimed_job" via the
#   (hidden) asset_job_keys parameter
# - the default sensor picks up the uncovered asset "uncovered" and the unclaimed
#   "unclaimed_job"
# Each entity must be evaluated by exactly one sensor.


@dg.asset(automation_condition=dg.AutomationCondition.missing())
def covered() -> None: ...


@dg.asset(automation_condition=dg.AutomationCondition.missing())
def uncovered() -> None: ...


@dg.asset
def claimed_member() -> None: ...


@dg.asset
def unclaimed_member() -> None: ...


claimed_job = dg.define_asset_job(
    "claimed_job",
    selection=[claimed_member],
    automation_condition=dg.AutomationCondition.all_job_root_assets_match(
        dg.AutomationCondition.missing()
    ),
)

unclaimed_job = dg.define_asset_job(
    "unclaimed_job",
    selection=[unclaimed_member],
    automation_condition=dg.AutomationCondition.all_job_root_assets_match(
        dg.AutomationCondition.missing()
    ),
)

defs = dg.Definitions(
    assets=[covered, uncovered, claimed_member, unclaimed_member],
    jobs=[claimed_job, unclaimed_job],
    sensors=[
        dg.AutomationConditionSensorDefinition(
            "explicit_sensor",
            target=[covered],
            asset_job_keys={dg.AssetJobKey(job_name="claimed_job")},
        )
    ],
)
