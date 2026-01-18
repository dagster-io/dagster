from dagster_pagerduty import PagerDutyService

import dagster as dg


@dg.asset
def pagerduty_alert(pagerduty: PagerDutyService):
    pagerduty.EventV2_create(
        summary="alert from dagster",
        source="localhost",
        severity="error",
        event_action="trigger",
    )


defs = dg.Definitions(
    assets=[pagerduty_alert],
    resources={
        "pagerduty": PagerDutyService(routing_key="0123456789abcdef0123456789abcdef")
    },
)
