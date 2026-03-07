---
title: incident.io webhook alerts
description: Create incidents using the incident.io API.
sidebar_position: 10
---

import EarlyAccess from '@site/docs/partials/\_EarlyAccess.md';

<EarlyAccess />

Automatically create incidents using the incident.io API.

## Step 1: Set up authentication credentials

Follow the [incident.io API guide](https://docs.incident.io/integrations/api-create-incident) to create an API key and fetch your severity configuration.

In your Dagster+ deployment settings, create an environment variable for the incident.io API key with a descriptive name (for example, `INCIDENT_IO_API_KEY`). Note the severity ID you'd like to use for alerts created by Dagster+.

## Step 2: Configure your alert notification

**Webhook Header**: In the Webhook configuration, set the following header:

- **Key**: `Authorization`
- **Value**: `Bearer {{env.INCIDENT_IO_API_KEY}}`

**Webhook URL**: Use `https://api.incident.io/v2/incidents` as the URL for your alert webhook.

**Webhook Body**:

```json
{
  "name": "{{alert_summary}}",
  "summary": "{{alert_content}}",
  "idempotency_key": "{{alert_policy_id}}:{{run_id}}",
  "severity_id": "YOUR_SEVERITY_ID",
  "visibility": "public"
}
```
