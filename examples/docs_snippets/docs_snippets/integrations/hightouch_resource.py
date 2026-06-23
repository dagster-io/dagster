from dagster_hightouch import (
    ConfigurableHightouchResource,  # ty: ignore[unresolved-import]
)

import dagster as dg

defs = dg.Definitions(
    resources={
        "hightouch": ConfigurableHightouchResource(
            api_key=dg.EnvVar("HIGHTOUCH_API_KEY"),
        )
    },
)
