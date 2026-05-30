import dagster as dg


@dg.asset(
    deps=[dg.AssetKey(["databricks_unity_catalog", "main", "raw", "events"])],
    automation_condition=dg.AutomationCondition.eager(),
)
def cleaned_events(): ...
