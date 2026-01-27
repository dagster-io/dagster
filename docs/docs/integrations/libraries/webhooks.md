---
title: Webhooks
description: Configure generic HTTP requests triggered by Dagster events to integrate with third-party services like Discord, Jira, and Linear.
sidebar_label: Webhooks
---

# Webhooks

Turn your Dagster alerts into actionable notifications. Webhooks allow Dagster+ to send HTTP requests to any endpoint when an event triggers, enabling deep integration with tools like Discord, Jira, Linear, and custom internal systems.

## Global Configuration

Navigate to **Deployment Settings > Alert Policies** to configure a webhook.

1.  **URL**: The destination HTTPS endpoint of your service.
2.  **Headers**: Custom headers required for authentication (e.g., `Authorization`, `X-Api-Key`).
3.  **Body**: Use the built-in JSON Editor to construct your payload using the template tokens below.

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
| Token | Description |
| :--- | :--- |
| `{{location_name}}` | Name of the code location. |
| `{{location_link}}` | URL to the code location. |
| `{{failure_message}}` | Error message describing the load failure. |

**Ticks (Schedules & Sensors)**
| Token | Description |
| :--- | :--- |
| `{{instigator_name}}` | Name of the schedule or sensor. |
| `{{instigator_type}}` | Type (`schedule` or `sensor`). |

**Agent Downtime**
| Token | Description |
| :--- | :--- |
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

---

## Platform Guide: Discord

This guide shows how to send rich, formatted notifications to a Discord channel using [Discord Webhooks](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks).

### 1. Setup

1.  Go to **Server Settings > Integrations > Webhooks**.
2.  Create a new Webhook and copy the **Webhook URL**.
3.  Paste this URL into the Dagster Alert Policy configuration.

### 2. Recommended Payload

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

### 3. Official References

- [Discord Webhooks Guide](https://discord.com/developers/docs/resources/webhook): Basic setup instructions.
- [Embed Object Structure](https://discord.com/developers/docs/resources/channel#embed-object): Customize colors, fields, and images.
- [Execute Webhook API](https://discord.com/developers/docs/resources/webhook#execute-webhook): Full API parameters documentation.

## Platform Guide: Jira Cloud

Automatically create bug tickets using the Jira Cloud REST API. [Jira Cloud REST API](https://id.atlassian.com/manage-profile/security/api-tokens)

### 1. Setup & Authentication

#### A. Determine your Endpoint

- **Simple Text (Recommended)**: Use API v2 for faster performance and lighter payloads.
  - **URL**: `https://<your-domain>.atlassian.net/rest/api/2/issue`
- **Rich Text**: Use API v3 if you strictly require ADF formatting (Heavier payload).
  - **URL**: `https://<your-domain>.atlassian.net/rest/api/3/issue`

#### B. Generate Credentials

Go to **Atlassian API Tokens** and create a token.

Jira requires Basic Auth encoded in Base64 (`email:token`).

**Mac/Linux Command**:

```bash
echo -n 'your_email@domain.com:your_api_token' | base64
```

**Dagster Header**: Set `Authorization` to `Basic <YOUR_BASE64_STRING>`.

### 2. Payloads

#### Option A: API v2 (Simple Text) - Recommended

Requires Endpoint v2. This is the most reliable method for automated alerts.

```json
{
  "fields": {
    "project": {"key": "ENG"},
    "issuetype": {"name": "Bug"},
    "priority": {"name": "High"},
    "summary": "Dagster: {{alert_summary}}",
    "description": "Error Details:\n{{alert_content}}\n\nLink: {{deployment_url}}"
  }
}
```

#### Option B: API v3 (Rich Text / ADF)

Requires Endpoint v3. Uses the Atlassian Document Format (ADF).

```json
{
  "fields": {
    "project": {"key": "ENG"},
    "issuetype": {"name": "Bug"},
    "priority": {"name": "High"},
    "summary": "Dagster: {{alert_summary}}",
    "description": {
      "type": "doc",
      "version": 1,
      "content": [
        {
          "type": "paragraph",
          "content": [
            {"type": "text", "text": "Details:\n", "marks": [{"type": "strong"}]},
            {"type": "text", "text": "{{alert_content}}", "marks": [{"type": "code"}]}
          ]
        },
        {
          "type": "paragraph",
          "content": [
            {
              "type": "text",
              "text": "View in Dagster",
              "marks": [{"type": "link", "attrs": {"href": "{{deployment_url}}"}}]
            }
          ]
        }
      ]
    }
  }
}
```

### 3. Official References

- [Jira REST API v2 (Legacy)](https://developer.atlassian.com/cloud/jira/platform/rest/v2/intro/): Reference for simple text payloads.
- [Jira REST API v3 (Latest)](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/): Reference for ADF payloads.
- [ADF Playground](https://developer.atlassian.com/cloud/jira/platform/apis/document/playground/): Tool to design and validate rich text JSON payloads.

## Platform Guide: Linear

Create issues directly via the Linear GraphQL API. (Note: Linear uses GraphQL, not standard REST webhooks). [Linear API](https://linear.app/settings/api)

### 1. Setup & Authentication

#### A. API Key

1.  Go to **Linear Settings > Account > API**.
2.  Create a **Personal API Key**.
3.  **Permission Check**: Ensure your key has `write` or `admin` scopes to perform issue creation mutations.
4.  **Dagster Header**: Set `Authorization` to `<YOUR_API_KEY>` (Do not add "Bearer").

#### B. Retrieve Team ID (UUID)

You must use the Team UUID (e.g., `8708e927...`), not the display name ("ENG"). Run this command in your terminal to find it:

```bash
curl -X POST https://api.linear.app/graphql \
  -H "Authorization: <YOUR_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"query": "query { teams { nodes { id name } } }"}'
```

### 2. Payload (GraphQL Mutation)

This payload creates an issue with a title, description, and link back to Dagster.

**Dagster URL**: `https://api.linear.app/graphql`

```json
{
  "query": "mutation CreateAlert($title: String!, $desc: String!, $team: String!) { issueCreate(input: { title: $title, description: $desc, teamId: $team, priority: 1 }) { success issue { url } } }",
  "variables": {
    "team": "YOUR_TEAM_UUID_HERE",
    "title": "{{alert_summary}}",
    "desc": "{{alert_content}}\n\n---\n**Source**: {{deployment_name}}\n**Policy**: {{alert_policy_name}}\n[Open Deployment]({{deployment_url}})"
  }
}
```

### 3. Official References

- [Linear GraphQL Schema](https://studio.apollographql.com/public/Linear-API/variant/current/home): Explorer to test queries and mutations.
- [Mutation: issueCreate](https://studio.apollographql.com/public/Linear-API/variant/current/schema/reference/objects/Mutation): Detailed docs on creating issues.
