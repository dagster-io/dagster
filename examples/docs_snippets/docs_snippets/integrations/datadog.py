from dagster_datadog import DatadogResource

import dagster as dg


@dg.asset
def report_to_datadog(datadog: DatadogResource):
    datadog_client = datadog.get_client()
    datadog_client.event("Man down!", "This server needs assistance.")  # ty: ignore[unresolved-attribute]
    datadog_client.gauge("users.online", 1001, tags=["protocol:http"])  # ty: ignore[unresolved-attribute]
    datadog_client.increment("page.views")  # ty: ignore[unresolved-attribute]


defs = dg.Definitions(
    assets=[report_to_datadog],
    resources={
        "datadog": DatadogResource(
            api_key=dg.EnvVar("DATADOG_API_KEY"),
            app_key=dg.EnvVar("DATADOG_APP_KEY"),
        )
    },
)
