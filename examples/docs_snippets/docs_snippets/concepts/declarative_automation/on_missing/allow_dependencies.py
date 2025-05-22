import dagster as dg

condition = dg.AutomationCondition.on_missing().allow(dg.AssetSelection.groups("abc"))
