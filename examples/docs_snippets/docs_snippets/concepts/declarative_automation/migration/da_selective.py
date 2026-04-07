import dagster as dg


@dg.asset(
    deps=["important_source", "static_config"],
    automation_condition=dg.AutomationCondition.eager().ignore(
        dg.AssetSelection.keys("static_config")
    ),
)
def downstream(): ...
