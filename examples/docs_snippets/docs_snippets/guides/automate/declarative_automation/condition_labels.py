import dagster as dg

in_progress_or_failed_deps = dg.AutomationCondition.any_deps_match(
    dg.AutomationCondition.in_progress() | dg.AutomationCondition.execution_failed()
).with_label("any_deps_in_progress_or_failed")
