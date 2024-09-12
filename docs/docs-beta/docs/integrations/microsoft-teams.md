---
layout: Integration
status: published
name: Microsoft Teams
title: Dagster & Microsoft Teams
sidebar_label: Microsoft Teams
excerpt: Keep your team up to speed with Teams messages.
date: 2024-08-30
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-msteams
docslink: 
partnerlink: https://www.microsoft.com/en-us/microsoft-teams/group-chat-software
logo: /integrations/Microsoft Teams.svg
categories:
  - Alerting
enabledBy:
enables:
---

### About this integration

By configuring this resource, you can post messages to MS Teams from any Dagster op or asset.

### Installation

```bash
pip install dagster-msteams
```

### Example

```python
# Read the docs on Resources to learn more: https://docs.dagster.io/deployment/resources
import dagster as dg
from dagster_msteams import Card, MSTeamsResource


@dg.asset
def microsoft_teams_message(msteams: MSTeamsResource):
    card = Card()
    card.add_attachment(text_message="Hello there!")
    msteams.get_client().post_message(payload=card.payload)


defs = dg.Definitions(
    assets=[microsoft_teams_message],
    resources={"msteams": MSTeamsResource(hook_url=dg.EnvVar("TEAMS_WEBHOOK_URL"))},
)
```

### About Microsoft Teams

**Microsoft Teams** is a business communication platform. Teams offers workspace chat and videoconferencing, file storage, and application integration.
