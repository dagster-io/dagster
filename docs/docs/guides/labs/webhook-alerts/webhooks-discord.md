---
title: Discord webhook alerts
description: Send notifications to a Discord channel using Discord Webhooks.
sidebar_position: 20
---

import EarlyAccess from '@site/docs/partials/\_EarlyAccess.md';

<EarlyAccess />

This guide shows how to send custom notifications to a Discord channel using [Discord Webhooks](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks).

## Step 1: Setup a webhook in Discord

1.  In Discord, go to **Server Settings > Integrations > Webhooks**.
2.  Create a new Webhook and copy the **Webhook URL**.
3.  [Recommended] Save the tokens at the end of the generated URL as a Dagster+ environment variable (e.g. `DISCORD_WEBHOOK_TOKEN`).
4.  Set the URL in the Alert Policy Webhook configuration (e.g. `https://discord.com/api/webhooks/{env.DISCORD_WEBHOOK_TOKEN}`)

## Step 2: Configure your webhook payload

This example utilizes Discord "Embeds" for rich formatting.

```json
{
  "username": "Dagster+ Alerts",
  "embeds": [
    {
      "title": "Alert: {{alert_summary}}",
      "url": "{{deployment_url}}",
      "description": "\n{{alert_content}}",
      "color": 15158332,
      "fields": [{"name": "Deployment", "value": "{{deployment_name}}", "inline": true}],
      "footer": {"text": "View alert policy: {{deployment_url}}/deployment/alerts/{{alert_policy_id}}"}
    }
  ]
}
```

## Official References

- [Discord Webhooks Guide](https://discord.com/developers/docs/resources/webhook): Basic setup instructions.
- [Embed Object Structure](https://discord.com/developers/docs/resources/channel#embed-object): Customize colors, fields, and images.
- [Execute Webhook API](https://discord.com/developers/docs/resources/webhook#execute-webhook): Full API parameters documentation.
