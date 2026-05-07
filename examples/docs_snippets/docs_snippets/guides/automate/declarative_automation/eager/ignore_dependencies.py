import dagster as dg

condition = dg.AutomationCondition.eager().ignore(dg.AssetSelection.assets("foo"))
