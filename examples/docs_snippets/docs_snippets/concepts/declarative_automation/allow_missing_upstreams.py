import dagster as dg

condition = (
    dg.AutomationCondition.eager()
    .without(~dg.AutomationCondition.any_deps_missing())
    .with_label("eager_allow_missing")
)
