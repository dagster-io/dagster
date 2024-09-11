---
layout: Integration
status: published
name: Slack
title: Dagster & Slack
sidebar_label: Slack
excerpt: Up your notification game and keep stakeholders in the loop.
date: 2024-08-30
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-slack
docslink: 
partnerlink: https://slack.com/
logo: /integrations/Slack.svg
categories:
  - Alerting
enabledBy:
enables:
---

### About this integration

This library provides an integration with Slack to support posting messages in your company's Slack workspace.

### Installation

```bash
pip install dagster-slack
```

### Example

```python
# Read the docs on Resources to learn more: https://docs.dagster.io/deployment/resources

import dagster as dg
from dagster_slack import SlackResource


@dg.asset
def slack_message(slack: SlackResource):
    slack.get_client().chat_postMessage(channel="#noise", text=":wave: hey there!")


defs = dg.Definitions(
    assets=[slack_message],
    resources={"slack": SlackResource(token=dg.EnvVar["SLACK_TOKEN"])},
)

```

### About Slack

The **Slack** messaging app provides chat, video and voice communication tools and is used extensively across companies and communities. The Dagster slack community can be found at [dagster.io/slack](https://dagster.io/slack).
