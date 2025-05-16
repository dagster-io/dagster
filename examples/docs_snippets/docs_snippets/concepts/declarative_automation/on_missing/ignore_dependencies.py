import dagster as dg

condition = dg.AutomationCondition.on_missing().ignore(dg.AssetSelection.assets("foo"))
