import numpy as np
import pandas as pd
from dagster_pipes import open_dagster_pipes

with open_dagster_pipes() as pipes:
    pipes.log.info("joining iot telem data in partition ({pipes.partition_key})....")
    data = pd.DataFrame(
        {
            "trace_id": range(1000),
            "trace_origin": np.random.choice(
                ["FoodCo", "ShopMart", "SportTime", "FamilyLtd"], size=1000
            ),
        }
    )
    pipes.report_asset_materialization(metadata={"row_count": len(data)})
