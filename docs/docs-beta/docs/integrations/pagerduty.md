---
layout: Integration
status: published
name: PagerDuty
title: Dagster & PagerDuty
sidebar_label: PagerDuty
excerpt: Centralize your monitoring with the dagster-pagerduty integration.
date: 2024-08-30
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-pagerduty
docslink: 
partnerlink: https://www.pagerduty.com/
logo: /integrations/PagerDuty.svg
categories:
  - Alerting
enabledBy:
enables:
---

### About this integration

This library provides an integration between Dagster and PagerDuty to support creating alerts from your Dagster code.

### Installation

```bash
pip install dagster_pagerduty
```

### Example

```python
import dagster as dg
from dagster_pagerduty import PagerDutyService


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

```

### About PagerDuty

**PagerDuty** is a popular SaaS incident response platform. It integrates machine data & human intelligence to improve visibility & agility for Real-Time Operations.
