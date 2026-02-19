---
description: Complete YAML reference for configuring alert policies in Dagster+, including event types, alert targets, notification services, and policy options.
sidebar_position: 500
tags: [dagster-plus-feature]
title: Alert policies YAML reference
---

import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';

<DagsterPlus />

This page provides a complete reference for configuring alert policies in Dagster+ via YAML.

## Top-level structure

```yaml
alert_policies:
  - name: 'policy-name' # Required: unique identifier
    description: '' # Optional: policy description
    enabled: true # Required: true/false
    event_types: # Required: list of events to trigger on
      - EVENT_TYPE
    alert_targets: # Optional: filter which entities trigger alerts
      - target_type: ...
    notification_service: # Required: how to deliver notifications
      service_type: ...
    policy_options: # Optional: additional configuration
      ...
```

---

## Event types

### Job events

| Event type         | Description                       |
| ------------------ | --------------------------------- |
| `JOB_FAILURE`      | Job run failed                    |
| `JOB_SUCCESS`      | Job run succeeded                 |
| `JOB_LONG_RUNNING` | Job running longer than threshold |

### Asset materialization and check events

| Event type                      | Description                           |
| ------------------------------- | ------------------------------------- |
| `ASSET_MATERIALIZATION_SUCCESS` | Asset materialization succeeded       |
| `ASSET_MATERIALIZATION_FAILURE` | Asset materialization failed          |
| `ASSET_CHECK_PASSED`            | Asset check passed                    |
| `ASSET_CHECK_EXECUTION_FAILURE` | Asset check execution failed          |
| `ASSET_CHECK_SEVERITY_WARN`     | Asset check returned warning severity |
| `ASSET_CHECK_SEVERITY_ERROR`    | Asset check returned error severity   |
| `ASSET_FRESHNESS_PASS`          | Asset freshness check passed          |
| `ASSET_FRESHNESS_WARN`          | Asset freshness check warning         |
| `ASSET_FRESHNESS_FAIL`          | Asset freshness check failed          |

### Asset health events

| Event type              | Description                             |
| ----------------------- | --------------------------------------- |
| `ASSET_HEALTH_HEALTHY`  | Asset health status changed to healthy  |
| `ASSET_HEALTH_WARNING`  | Asset health status changed to warning  |
| `ASSET_HEALTH_DEGRADED` | Asset health status changed to degraded |

### Asset schema events

| Event type                  | Description                |
| --------------------------- | -------------------------- |
| `ASSET_TABLE_SCHEMA_CHANGE` | Asset table schema changed |

### Schedule and sensor events

| Event type     | Description                    |
| -------------- | ------------------------------ |
| `TICK_FAILURE` | Schedule or sensor tick failed |

### Infrastructure events

| Event type            | Description                  |
| --------------------- | ---------------------------- |
| `AGENT_UNAVAILABLE`   | Agent became unavailable     |
| `CODE_LOCATION_ERROR` | Code location failed to load |

### Insights and metrics events

| Event type                      | Description                       |
| ------------------------------- | --------------------------------- |
| `INSIGHTS_CONSUMPTION_EXCEEDED` | Consumption exceeded threshold    |
| `METRIC_MONITOR_ALERT`          | Metric monitor threshold exceeded |

---

## Alert targets

### For job events

#### Run result target

Optional filtering for job run alerts.

```yaml
alert_targets:
  - run_result_target:
      jobs: # Optional: specific jobs
        - location_name: loc
          repo_name: __repository__
          job_name: my_job
      tags: # Optional: filter by run tags
        - key: team
          value: ml
      location_names: # Optional: filter by code location
        - location_name
```

#### Long-running job target

Required for `JOB_LONG_RUNNING` event type.

```yaml
alert_targets:
  - long_running_job_threshold_target:
      threshold_seconds: 900 # Required: duration threshold
      jobs: # Optional: specific jobs
        - location_name: loc
          repo_name: __repository__
          job_name: my_job
      tags: # Optional: filter by run tags
        - key: team
          value: ml
      location_names: # Optional: filter by code location
        - location_name
```

### For asset events

#### Single asset target

```yaml
alert_targets:
  - asset_key_target:
      asset_key:
        - NAMESPACE
        - asset_name
```

#### Asset selection target

Uses Dagster's asset selection syntax.

```yaml
alert_targets:
  - asset_selection_target:
      asset_selection: '*' # All assets
      # asset_selection: 'group:"group_name"'
      # asset_selection: 'tag:key=value'
      # asset_selection: 'owner:"team@example.com"'
```

#### Asset group target

```yaml
alert_targets:
  - asset_group_target:
      asset_group: group_name
      location_name: loc
      repo_name: __repository__
```

#### Saved catalog view target

```yaml
alert_targets:
  - asset_selection_view_target:
      asset_selection_view_id: 'view-id'
```

#### User favorites target

```yaml
alert_targets:
  - favorites_selection_view_target:
      user_email: user@example.com
```

### For schedule and sensor events

```yaml
alert_targets:
  - schedule_or_sensor_target:
      schedules_or_sensors: # Optional: specific schedules/sensors
        - location_name: loc
          repo_name: __repository__
          name: my_schedule
      location_names: # Optional: filter by code location
        - location_name
      types: # Optional: filter by type
        - SCHEDULE
        - SENSOR
```

### For code location events

```yaml
alert_targets:
  - code_location_target:
      location_names: # Optional: specific locations (omit for all)
        - batch_enrichment
```

### For insights events

#### Organization credit limit

```yaml
alert_targets:
  - credit_limit_target: {}
```

#### Deployment-wide metric

```yaml
alert_targets:
  - insights_deployment_threshold_target:
      metric_name: '__dagster_dagster_credits'
      selection_period_days: 30
      threshold: 1000
      operator: GREATER_THAN # or LESS_THAN
```

#### Asset group metric

```yaml
alert_targets:
  - insights_asset_group_threshold_target:
      metric_name: '__dagster_dagster_credits'
      selection_period_days: 7
      threshold: 100
      operator: GREATER_THAN # or LESS_THAN
      asset_group:
        location_name: loc
        repo_name: __repository__
        asset_group_name: group
```

#### Single asset metric

```yaml
alert_targets:
  - insights_asset_threshold_target:
      metric_name: '__dagster_dagster_credits'
      selection_period_days: 7
      threshold: 100
      operator: GREATER_THAN # or LESS_THAN
      asset_key:
        - NAMESPACE
        - asset
```

#### Job metric

```yaml
alert_targets:
  - insights_job_threshold_target:
      metric_name: '__dagster_dagster_credits'
      selection_period_days: 7
      threshold: 100
      operator: GREATER_THAN # or LESS_THAN
      job:
        location_name: loc
        repo_name: __repository__
        job_name: my_job
```

### For metric monitor events

```yaml
alert_targets:
  - metric_monitor_asset_selection_threshold_target:
      metric_name: '__dagster_asset_check_warnings'
      lookback_window: 24 # Hours
      aggregation_function: max # sum, latest, max, min
      asset_selection: '*'
      combine_fn: ANY # ANY or ALL
      thresholds:
        min_allowed_value: 5 # At least one threshold required
        max_allowed_value: 100 # At least one threshold required
```

---

## Notification services

### Email

```yaml
notification_service:
  email:
    email_addresses:
      - user@example.com
      - team@example.com
```

### Email to asset owners

Sends notifications to asset owners defined in asset metadata. Only valid for asset-related alerts.

```yaml
notification_service:
  email_owners:
    default_email_addresses: # Optional: fallback if asset has no owner
      - fallback@example.com
```

### Slack

```yaml
notification_service:
  slack:
    slack_workspace_name: workspace
    slack_channel_name: channel
```

### Microsoft Teams

```yaml
notification_service:
  microsoft_teams:
    webhook_url: 'https://outlook.webhook.office.com/webhookb2/...'
```

### PagerDuty

```yaml
notification_service:
  pagerduty:
    integration_key: 'your-integration-key'
```

---

## Policy options

```yaml
policy_options:
  # Include asset/policy description in notification body
  include_description_in_notification: true

  # For TICK_FAILURE only: number of consecutive failures before alerting (1-100)
  consecutive_failure_threshold: 3

  # For TICK_FAILURE, AGENT_UNAVAILABLE, CODE_LOCATION_ERROR:
  # Re-notify every N minutes while issue persists (>= 1)
  renotify_interval_minutes: 60

  # For ASSET_TABLE_SCHEMA_CHANGE only (at least one required):
  table_schema_change_types:
    - COLUMN_ADDED
    - COLUMN_REMOVED
    - COLUMN_TYPE_CHANGED
    - COLUMN_NULLABILITY_CHANGED
    - COLUMN_UNIQUENESS_CHANGED
    - COLUMN_TAGS_CHANGED
```

---

## Validation rules

1. **Event type compatibility**: All event types in a single policy must belong to the same category (job, asset, schedule/sensor, infrastructure, or insights).

2. **Asset event exclusivity**: Asset-related events cannot be mixed:

   - Materialization/check events (`ASSET_MATERIALIZATION_*`, `ASSET_CHECK_*`, `ASSET_FRESHNESS_*`)
   - Health events (`ASSET_HEALTH_*`)
   - Schema events (`ASSET_TABLE_SCHEMA_CHANGE`)

3. **Long-running job requirements**: `JOB_LONG_RUNNING` event type requires a `long_running_job_threshold_target` with `threshold_seconds` specified.

4. **Table schema change requirements**: `ASSET_TABLE_SCHEMA_CHANGE` event type requires at least one entry in `policy_options.table_schema_change_types`.

5. **Insights/Metric alert targets**: Policies with `INSIGHTS_*` or `METRIC_MONITOR_ALERT` event types require exactly one alert target.

6. **Empty alert targets**: An empty `alert_targets: []` list means the policy applies to all entities of that type.

7. **Consecutive failure threshold**: Only valid for `TICK_FAILURE` events. Must be between 1 and 100.

8. **Renotify interval**: Only valid for `TICK_FAILURE`, `AGENT_UNAVAILABLE`, and `CODE_LOCATION_ERROR` events. Must be >= 1 minute.

9. **Email owners notification**: Only valid for asset-related alerts where assets have owners defined.

---

## Complete examples

### Agent downtime alert

```yaml
alert_policies:
  - name: agent downtime alert
    description: 'Alert when agent becomes unavailable'
    event_types:
      - AGENT_UNAVAILABLE
    notification_service:
      email:
        email_addresses:
          - ops@example.com
    enabled: true
    alert_targets: []
    policy_options:
      include_description_in_notification: true
      renotify_interval_minutes: 30
```

### Job alerts with tag filtering

```yaml
alert_policies:
  - name: ml team job alerts
    description: 'Alert ML team on their job failures'
    event_types:
      - JOB_SUCCESS
      - JOB_FAILURE
      - JOB_LONG_RUNNING
    notification_service:
      slack:
        slack_workspace_name: mycompany
        slack_channel_name: ml-alerts
    enabled: true
    alert_targets:
      - long_running_job_threshold_target:
          tags:
            - key: team
              value: ml
          threshold_seconds: 900
    policy_options:
      include_description_in_notification: true
```

### Asset health monitoring

```yaml
alert_policies:
  - name: asset health alerts
    description: 'Monitor asset health status changes'
    event_types:
      - ASSET_HEALTH_DEGRADED
      - ASSET_HEALTH_WARNING
      - ASSET_HEALTH_HEALTHY
    notification_service:
      email_owners:
        default_email_addresses:
          - data-team@example.com
    enabled: true
    alert_targets:
      - asset_selection_target:
          asset_selection: 'group:"critical_assets"'
    policy_options:
      include_description_in_notification: true
```

### Schedule and sensor failure alerts

```yaml
alert_policies:
  - name: automation failure alerts
    description: 'Alert on consecutive automation failures'
    event_types:
      - TICK_FAILURE
    notification_service:
      pagerduty:
        integration_key: 'your-pagerduty-key'
    enabled: true
    alert_targets:
      - schedule_or_sensor_target:
          schedules_or_sensors:
            - location_name: data-eng-pipeline
              repo_name: __repository__
              name: critical_schedule
    policy_options:
      consecutive_failure_threshold: 3
      include_description_in_notification: true
```

### Table schema change monitoring

```yaml
alert_policies:
  - name: schema change alerts
    description: 'Alert on table schema changes'
    event_types:
      - ASSET_TABLE_SCHEMA_CHANGE
    notification_service:
      email_owners:
        default_email_addresses:
          - data-governance@example.com
    enabled: true
    alert_targets:
      - asset_key_target:
          asset_key:
            - ANALYTICS
            - company_perf
    policy_options:
      include_description_in_notification: true
      table_schema_change_types:
        - COLUMN_TYPE_CHANGED
        - COLUMN_REMOVED
        - COLUMN_NULLABILITY_CHANGED
```

### Custom metric monitoring

```yaml
alert_policies:
  - name: asset check warning monitor
    description: 'Alert when asset check warnings exceed threshold'
    event_types:
      - METRIC_MONITOR_ALERT
    notification_service:
      email:
        email_addresses:
          - data-quality@example.com
    enabled: true
    alert_targets:
      - metric_monitor_asset_selection_threshold_target:
          metric_name: __dagster_asset_check_warnings
          lookback_window: 24
          thresholds:
            min_allowed_value: 5
          aggregation_function: max
          asset_selection: '*'
          combine_fn: ANY
    policy_options:
      include_description_in_notification: true
```
