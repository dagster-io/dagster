from dagster_hightouch import ConfigurableHightouchResource

import dagster as dg

defs = dg.Definitions(
    resources={
        "hightouch": ConfigurableHightouchResource(
            api_key=dg.EnvVar("HIGHTOUCH_API_KEY"),
        )
    },
)
