import dagster as dg

# start_all_deps_custom
all_deps_updated_since_target = (
    dg.AutomationCondition.all_deps_match(
        dg.AutomationCondition.newly_updated().since(
            dg.AutomationCondition.asset_matches(
                "my_downstream_asset",
                dg.AutomationCondition.newly_requested()
                | dg.AutomationCondition.newly_updated(),
            )
        )
    )
    & ~dg.AutomationCondition.in_progress()
)
# end_all_deps_custom
