---
layout: Integration
status: published
name: Twilio
title: Dagster & Twilio
sidebar_label: Twilio
excerpt: Integrate Twilio tasks into your data pipeline runs.
date: 2024-08-30
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-twilio
docslink: 
partnerlink: https://www.twilio.com/
logo: /integrations/Twilio.svg
categories:
  - Alerting
enabledBy:
enables:
---

### About this integration

Use your Twilio `Account SID` and `Auth Token` to build Twilio tasks right into your Dagster pipeline.

### Installation

```bash
pip install dagster-twilio
```

### Example

```python
# Read the docs on Resources to learn more: https://docs.dagster.io/deployment/resources
import dagster as dg
from dagster_twilio import TwilioResource


@dg.asset
def twilio_message(twilio: TwilioResource):
    twilio.get_client().messages.create(
        to="+15551234567", from_="+15558901234", body="Hello world!"
    )


defs = dg.Definitions(
    assets=[twilio_message],
    resources={
        "twilio": TwilioResource(
            account_sid=dg.EnvVar("TWILIO_ACCOUNT_SID"),
            auth_token=dg.EnvVar("TWILIO_AUTH_TOKEN"),
        )
    },
)
```

### About Twilio

**Twilio** provides communication APIs for phone calls, text messages, and other communication functions.
