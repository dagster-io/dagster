import dagster as dg

condition = dg.AutomationCondition.eager().resolve_through_virtual()
