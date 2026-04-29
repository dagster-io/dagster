---
title: Webhook alert notifications
sidebar_label: Webhooks
description: Configure generic HTTP requests triggered by Dagster alerts to integrate with any third-party service.
canonicalUrl: '/guides/labs/webhook-alerts'
slug: '/guides/labs/webhook-alerts'
sidebar_position: 40
---

import EarlyAccess from '@site/docs/partials/\_EarlyAccess.md';

<EarlyAccess />

Dagster+ alerts can be configured to send HTTP requests to any endpoint when an alert is triggered, enabling deep integration with chat clients, task management tools, incident management software, or custom internal systems.

## Configuration

Navigate to **Deployment Settings > Alert Policies** to configure a webhook.

1.  **URL**: The destination HTTPS endpoint of your service.
2.  **Headers**: Custom headers (e.g., `Authorization`, `X-Api-Key`).
3.  **Body**: Use the built-in JSON Editor to construct your payload using the template tokens below.

We suggest storing secrets, such as API keys, as [environment variables](/deployment/dagster-plus/management/environment-variables) and including them in the webhook using [template tokens](#environment-variable-tokens).

## Domain whitelist (Early Access limitation)

During the Early Access period, we are limiting outgoing webhooks to a whitelisted set of domains. Please let us know which domains you'd like to send webhooks to.

## Example webhook configurations

Use these guides to get started using webhooks with these common services:

- [Jira](/guides/labs/webhook-alerts/webhooks-jira)
- [Discord](/guides/labs/webhook-alerts/webhooks-discord)
- [incident.io](/guides/labs/webhook-alerts/webhooks-incidentio)

## Token reference

Dagster provides dynamic tokens that are replaced with actual event data at runtime. Token availability depends on the **Event Type**.

### Globally available tokens

These tokens are available for **every** notification type.

| Token                          | Description                                          | Example                          |
| :----------------------------- | :--------------------------------------------------- | :------------------------------- |
| `{{alert_summary}}`            | **Recommended**. One-line summary of the alert.      | `Job daily_etl failed`           |
| `{{alert_content}}`            | **Recommended**. Full alert details (errors, links). | `Error: Step failed...`          |
| `{{deployment_name}}`          | Name of the Dagster deployment.                      | `prod`                           |
| `{{deployment_url}}`           | URL to the Dagster deployment.                       | `https://dagster.cloud/...`      |
| `{{alert_policy_name}}`        | Name of the alert policy that triggered.             | `Critical Alerts`                |
| `{{alert_policy_id}}`          | Unique ID of the alert policy.                       | `abc123-def456`                  |
| `{{alert_policy_description}}` | Description of the alert policy.                     | `Alerts when production jobs...` |
| `{{alert_id}}`                 | Unique ID of the alert.                              | `abc123-def456`                  |
| `{{notification_type}}`        | Type of notification event (e.g., `JOB`, `TICK`).    | `JOB`                            |
| `{{is_sample}}`                | `true` if this is a test/sample notification.        | `false`                          |

### Environment variable tokens

You can access environment variables, such as `{{env.WEBHOOK_API_KEY}}`, to avoid hardcoding secrets. See [Environment Variables](/deployment/dagster-plus/management/environment-variables) for setup instructions.

### Job and run tokens

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

### Asset event tokens

Available for **Asset Materialization**, **Asset Check**, and **Asset Freshness Policy** events. A single alert can span multiple assets and multiple event types, so the asset and event-type tokens expose collections.

| Token                        | Description                                                                                     | Available for          | Example                                                        |
| :--------------------------- | :---------------------------------------------------------------------------------------------- | :--------------------- | :------------------------------------------------------------- |
| `{{asset_keys}}`             | Comma-separated list of asset keys affected by this alert.                                      | All                    | `orders, customers`                                            |
| `{{asset_keys_json}}`        | JSON array of asset keys affected by this alert.                                                | All                    | `["orders", "customers"]`                                      |
| `{{event_types}}`            | Comma-separated human-readable labels of the asset event types in this alert.                   | All                    | `Asset materializations failed, Asset check executions failed` |
| `{{event_type_counts_json}}` | JSON object mapping raw asset event type names to counts in this alert.                         | All                    | `{"ASSET_MATERIALIZATION_FAILURE": 3}`                         |
| `{{run_id}}`                 | Unique ID of the run that produced the event.                                                   | Materialization, Check | `abc123`                                                       |
| `{{run_link}}`               | URL to view the run in Dagster.                                                                 | Materialization, Check | `https://dagster.cloud/acme/prod/runs/abc123`                  |
| `{{failure_message}}`        | Error message describing the failure.                                                           | Materialization, Check | `Asset materialization failed`                                 |
| `{{user_name}}`              | Name of the user who launched the run.                                                          | Materialization, Check | `John Doe`                                                     |
| `{{user_email}}`             | Email of the user who launched the run.                                                         | Materialization, Check | `john@example.com`                                             |
| `{{freshness_status}}`       | Freshness policy health status (`HEALTHY`, `WARNING`, `DEGRADED`, `UNKNOWN`, `NOT_APPLICABLE`). | Freshness policy       | `DEGRADED`                                                     |

### Asset health tokens

Available for **Asset Health** events.

All status tokens can be one of: `HEALTHY`, `WARNING`, `DEGRADED`, `UNKNOWN`, or `NOT_APPLICABLE`.

| Token                        | Description                    | Example    |
| :--------------------------- | :----------------------------- | :--------- |
| `{{asset_key}}`              | Full asset key.                | `orders`   |
| `{{health_status}}`          | Overall health status.         | `DEGRADED` |
| `{{materialization_status}}` | Materialization health status. | `HEALTHY`  |
| `{{checks_status}}`          | Asset checks health status.    | `WARNING`  |
| `{{freshness_status}}`       | Freshness health status.       | `UNKNOWN`  |

### Table schema tokens

| Token                             | Description                                                             |
| :-------------------------------- | :---------------------------------------------------------------------- |
| `{{asset_key}}`                   | Full asset key of the asset whose schema changed.                       |
| `{{columns_added}}`               | List of newly added column names.                                       |
| `{{columns_removed}}`             | List of removed column names.                                           |
| `{{columns_type_changed}}`        | List of `[column, old_type, new_type]` for type changes.                |
| `{{columns_nullability_changed}}` | List of `[column, old_nullable, new_nullable]` for nullability changes. |
| `{{columns_uniqueness_changed}}`  | List of `[column, old_unique, new_unique]` for uniqueness changes.      |
| `{{columns_tags_changed}}`        | List of `[column, old_tags, new_tags]` for tag changes.                 |

### Code location tokens

| Token                 | Description                                |
| :-------------------- | :----------------------------------------- |
| `{{location_name}}`   | Name of the code location.                 |
| `{{location_link}}`   | URL to the code location.                  |
| `{{failure_message}}` | Error message describing the load failure. |

### Tick (schedules and sensors) tokens

| Token                 | Description                                               |
| :-------------------- | :-------------------------------------------------------- |
| `{{instigator_name}}` | Name of the schedule or sensor.                           |
| `{{instigator_type}}` | Type (`schedule` or `sensor`).                            |
| `{{schedule_name}}`   | Name of the schedule (empty if this is a sensor failure). |
| `{{sensor_name}}`     | Name of the sensor (empty if this is a schedule failure). |

### Agent downtime tokens

| Token           | Description                        |
| :-------------- | :--------------------------------- |
| `{{agent_url}}` | URL to the agents page in Dagster. |

### Metric monitor tokens

| Token             | Description                          |
| :---------------- | :----------------------------------- |
| `{{metric_name}}` | Name of the monitored metric.        |
| `{{target_desc}}` | Description of the monitored target. |
