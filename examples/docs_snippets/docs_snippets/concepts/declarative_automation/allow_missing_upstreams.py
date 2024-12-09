import dagster as dg

condition = (
    dg.AutomationCondition.eager()
    .without(~dg.AutomationCondition.missing())
    .with_label("eager_allow_missing")
)
