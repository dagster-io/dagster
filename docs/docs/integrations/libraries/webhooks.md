---
title: Webhook alert notifications
description: Configure generic HTTP requests triggered by Dagster alerts to integrate with any third-party service.
sidebar_label: Webhooks
---

import Beta from '@site/docs/partials/_Beta.md';

<Beta />

# Webhooks

Dagster+ alerts can be configured to send HTTP requests to any endpoint when an alert is triggered, enabling deep integration with chat clients, task management tools, incident management software, or custom internal systems.

## Global Configuration

Navigate to **Deployment Settings > Alert Policies** to configure a webhook.

1.  **URL**: The destination HTTPS endpoint of your service.
2.  **Headers**: Custom headers required for authentication (e.g., `Authorization`, `X-Api-Key`).
3.  **Body**: Use the built-in JSON Editor to construct your payload using the template tokens below.

---

## Example Webhook Configurations

### Discord

This guide shows how to send rich, formatted notifications to a Discord channel using [Discord Webhooks](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks).

#### 1. Setup

1.  Go to **Server Settings > Integrations > Webhooks**.
2.  Create a new Webhook and copy the **Webhook URL**.
3.  Paste this URL into the Dagster Alert Policy configuration.

#### 2. Recommended Payload

This payload utilizes Discord "Embeds" for a professional look and includes variable spam protection.

````json
{
  "username": "Dagster Monitor",
  "avatar_url": "https://dagster.io/images/brand/logos/dagster-primary.png",
  "content": "**Alert Triggered**: {{alert_summary}}",
  "embeds": [
    {
      "title": "{{alert_summary}}",
      "url": "{{run_link}}",
      "description": "```\n{{alert_content}}\n```",
      "color": 15158332,
      "fields": [
        {"name": "Deployment", "value": "{{deployment_name}}", "inline": true},
        {"name": "Policy", "value": "{{alert_policy_name}}", "inline": true}
      ],
      "footer": {"text": "Dagster+ • {{deployment_url}}"},
      "timestamp": "{{start_time}}"
    }
  ]
}
````

> **Pro Tip**: To tag a specific role (e.g., `@Engineers`), add `<@&ROLE_ID>` to the `content` field.

#### 3. Official References

- [Discord Webhooks Guide](https://discord.com/developers/docs/resources/webhook): Basic setup instructions.
- [Embed Object Structure](https://discord.com/developers/docs/resources/channel#embed-object): Customize colors, fields, and images.
- [Execute Webhook API](https://discord.com/developers/docs/resources/webhook#execute-webhook): Full API parameters documentation.

### Slack

Send rich, interactive alerts using Slack Apps (Incoming Webhooks). This is the modern replacement for legacy custom integrations.

#### 1. Setup

Go to Slack API: Your Apps and click **Create New App** > **From scratch**. [Slack App](https://api.slack.com/apps)

1.  Name your app (e.g., "Dagster Alerts") and select your workspace.
2.  In the left sidebar, click **Incoming Webhooks** and toggle **Activate Incoming Webhooks** to **On**.
3.  Click **Add New Webhook to Workspace**, select the target channel, and authorize.
4.  Copy the Webhook URL (e.g., `https://hooks.slack.com/services/T000.../B000.../XXXX`).

#### 2. Dagster Configuration

- **URL**: Paste your Webhook URL.
- **Headers**: None required (Authentication is embedded in the URL).

#### 3. Payload (Block Kit)

Slack Block Kit allows for structured layouts and interactive buttons.

**Key Requirements:**

- **Header Blocks**: Must use `"type": "plain_text"`.
- **Mentions**: Use `<@USER_ID>` for users or `<!subteam^GROUP_ID>` for user groups.
- **Color**: Use `"style": "danger"` on buttons to indicate errors (Side-bar colors are deprecated in Block Kit).

**Recommended JSON Template:**

````json
{
  "text": "{{alert_summary}}",
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "Dagster Alert: {{alert_policy_name}}",
        "emoji": true
      }
    },
    {
      "type": "section",
      "fields": [
        {
          "type": "mrkdwn",
          "text": "*Deployment:*\n{{deployment_name}}"
        },
        {
          "type": "mrkdwn",
          "text": "*Alert Policy:*\n{{alert_policy_name}}"
        }
      ]
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Error Summary:*\n{{alert_summary}}"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Details:*\n```{{alert_content}}```"
      }
    },
    {
      "type": "actions",
      "elements": [
        {
          "type": "button",
          "text": {
            "type": "plain_text",
            "text": "View in Dagster",
            "emoji": true
          },
          "url": "{{deployment_url}}",
          "style": "danger"
        }
      ]
    }
  ]
}
````

#### 4. Official References

- [Block Kit Builder](https://app.slack.com/block-kit-builder): Prototyping tool to design and preview your payload.
- [Mentions Syntax](https://api.slack.com/reference/surfaces/formatting#formatting-mentions): Guide on formatting user and group mentions.
- [Rate Limits](https://api.slack.com/rtm#rate_limiting): Slack allows 1 request per second (with short bursts). Exceeding this returns HTTP 429.

---

## Token Reference

Dagster provides dynamic tokens that are replaced with actual event data at runtime. Token availability depends on the **Event Type**.

### Global Tokens (Always Available)

These tokens are available for **every** notification type.

| Token                   | Description                                          | Example                     |
| :---------------------- | :--------------------------------------------------- | :-------------------------- |
| `{{alert_summary}}`     | **Recommended**. One-line summary of the alert.      | `Job daily_etl failed`      |
| `{{alert_content}}`     | **Recommended**. Full alert details (errors, links). | `Error: Step failed...`     |
| `{{deployment_name}}`   | Name of the Dagster deployment.                      | `prod`                      |
| `{{deployment_url}}`    | URL to the Dagster deployment.                       | `https://dagster.cloud/...` |
| `{{alert_policy_name}}` | Name of the alert policy that triggered.             | `Critical Alerts`           |
| `{{alert_policy_id}}`   | Unique ID of the alert policy.                       | `abc123-def456`             |
| `{{notification_type}}` | Type of notification event (e.g., `JOB`, `TICK`).    | `JOB`                       |
| `{{is_sample}}`         | `true` if this is a test/sample notification.        | `false`                     |

### Job & Run Tokens

Available for **Job** events (Success, Failure, Long-running).

| Token                 | Description                                  | Example                      |
| :-------------------- | :------------------------------------------- | :--------------------------- |
| `{{job_name}}`        | Name of the job.                             | `daily_etl`                  |
| `{{run_id}}`          | Unique ID of the run.                        | `abc123-def456`              |
| `{{run_link}}`        | URL to view the run in Dagster.              | `.../runs/abc123`            |
| `{{run_status}}`      | Status (`SUCCESS` or `FAILURE`).             | `FAILURE`                    |
| `{{failure_message}}` | Error message if the run failed.             | `Step 'load_data' failed...` |
| `{{user_name}}`       | Name of the user who launched the run.       | `John Doe`                   |
| `{{user_email}}`      | Email of the user who launched the run.      | `john@example.com`           |
| `{{partition_name}}`  | Name of the partition (if applicable).       | `2026-01-08`                 |
| `{{schedule_name}}`   | Name of the schedule that triggered the run. | `daily_schedule`             |
| `{{sensor_name}}`     | Name of the sensor that triggered the run.   | `new_files_sensor`           |
| `{{elapsed_time}}`    | Human-readable duration of the run.          | `5 minutes`                  |
| `{{start_time}}`      | Start time of the run.                       | `Jan 8, 2026 10:00 AM`       |
| `{{end_time}}`        | End time of the run.                         | `Jan 8, 2026 10:05 AM`       |

### Asset Tokens

Tokens specific to Asset events.

<details>
<summary><strong>View Asset Materialization Tokens</strong></summary>

Available for **Asset Materialization** events (Success/Failure/Check Failure).

| Token                 | Description                             |
| :-------------------- | :-------------------------------------- |
| `{{run_id}}`          | Unique ID of the run.                   |
| `{{run_link}}`        | URL to view the run in Dagster.         |
| `{{failure_message}}` | Error message describing the failure.   |
| `{{user_name}}`       | Name of the user who launched the run.  |
| `{{user_email}}`      | Email of the user who launched the run. |

</details>

<details>
<summary><strong>View Asset Health & Freshness Tokens</strong></summary>

Available for **Asset Health**, **Freshness**, and **Table Schema** events.

| Token                        | Description                              | Context            |
| :--------------------------- | :--------------------------------------- | :----------------- |
| `{{asset_key}}`              | Full asset key.                          | All Asset Events   |
| `{{asset_name}}`             | Name of the asset.                       | All Asset Events   |
| `{{health_status}}`          | Overall status (`OK`, `DEGRADED`).       | Asset Health       |
| `{{materialization_status}}` | Status of materialization.               | Asset Health       |
| `{{checks_status}}`          | Status of asset checks.                  | Asset Health       |
| `{{freshness_status}}`       | State (`PASS`, `FAIL`, `UNKNOWN`, `OK`). | Freshness / Health |

</details>

### System & Infrastructure Tokens

Tokens for advanced system monitoring.

<details>
<summary><strong>View Code Location, Agent & Tick Tokens</strong></summary>

**Code Locations**

| Token                 | Description                                |
| :-------------------- | :----------------------------------------- |
| `{{location_name}}`   | Name of the code location.                 |
| `{{location_link}}`   | URL to the code location.                  |
| `{{failure_message}}` | Error message describing the load failure. |

**Ticks (Schedules & Sensors)**

| Token                 | Description                     |
| :-------------------- | :------------------------------ |
| `{{instigator_name}}` | Name of the schedule or sensor. |
| `{{instigator_type}}` | Type (`schedule` or `sensor`).  |

**Agent Downtime**

| Token           | Description                        |
| :-------------- | :--------------------------------- |
| `{{agent_url}}` | URL to the agents page in Dagster. |

</details>

### Insights Tokens

Available when **Dagster Insights** alerts are triggered (e.g., consumption exceeded).

<details>
<summary><strong>View Insights Tokens</strong></summary>

| Token                | Description                  | Example           |
| :------------------- | :--------------------------- | :---------------- |
| `{{metric_name}}`    | Internal name of the metric. | `dagster_credits` |
| `{{threshold}}`      | Configured threshold value.  | `1000`            |
| `{{computed_value}}` | Actual computed value.       | `1250`            |
| `{{insights_url}}`   | URL to the insights page.    |                   |

</details>
