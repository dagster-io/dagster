import dagster as dg


@dg.asset
def raw_data() -> None: ...


@dg.asset(deps=[raw_data])
def processed_data() -> None: ...


@dg.asset(deps=[processed_data])
def report() -> None: ...


analytics_job = dg.define_asset_job(
    "analytics_job",
    selection=[processed_data, report],
    automation_condition=dg.AutomationCondition.all_job_root_assets_match(
        dg.AutomationCondition.eager()
    ),
)
