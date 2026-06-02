import dagster as dg

condition = dg.AutomationCondition.eager().allow(dg.AssetSelection.groups("abc"))
