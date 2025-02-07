import dagster as dg

condition = dg.AutomationCondition.eager().replace("newly_updated")
