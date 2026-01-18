import dagster as dg


@dg.asset
def root() -> None: ...


@dg.asset(deps=[root], automation_condition=dg.AutomationCondition.eager())
def downstream() -> None: ...


defs = dg.Definitions(assets=[root, downstream])
