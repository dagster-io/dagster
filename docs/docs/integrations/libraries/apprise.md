---
title: Dagster & Apprise
sidebar_label: Apprise
description: Send notifications across 70+ notification services (Discord, Telegram, Jira, email, and more) from Dagster using the Apprise library.
tags: [community-supported, alerting]
source: https://github.com/dagster-io/community-integrations/tree/main/libraries/dagster-apprise
pypi: https://pypi.org/project/dagster-apprise/
sidebar_custom_props:
  logo: images/integrations/apprise.png
  community: true
partnerlink: https://github.com/caronc/apprise
---

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-apprise" />

## Example

```python
import dagster as dg
from dagster_apprise import apprise_notifications, AppriseNotificationsConfig

# Configure notifications
config = AppriseNotificationsConfig(
    urls=["discord://webhook_id/webhook_token"], # Discord notification, details should be secure
    events=["SUCCESS", "FAILURE"],  # What to notify about
    include_jobs=["*"],  # All jobs
)

# Add to your Dagster definitions
defs = dg.Definitions(
    assets=[your_assets],
    jobs=[your_jobs],
    **apprise_notifications(config).to_dict()
)
```

Alternatively, you can configure notifications in `defs.yaml` using the Apprise URL(s) for your destination(s).

```yaml
type: dagster_apprise.apprise_notifications

attributes:
  urls:
    - 'discord://WEBHOOK_ID/WEBHOOK_TOKEN'
    # - "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    # - "mailto://user:pass@gmail.com"
  events: ['FAILURE']
  include_jobs: ['*']
  base_url: 'http://localhost:3000'
```

## Configuration Options

### Full List

See the [Apprise documentation](https://github.com/caronc/apprise/wiki) for all supported services.

### AppriseNotificationsConfig

| Option         | Type        | Default       | Description                       |
| -------------- | ----------- | ------------- | --------------------------------- |
| `urls`         | `list[str]` | `[]`          | List of Apprise notification URLs |
| `config_file`  | `str`       | `None`        | Path to Apprise config file       |
| `base_url`     | `str`       | `None`        | Base URL for Dagster UI links     |
| `title_prefix` | `str`       | `"Dagster"`   | Prefix for notification titles    |
| `events`       | `list[str]` | `["FAILURE"]` | Events to notify about            |
| `include_jobs` | `list[str]` | `["*"]`       | Job patterns to include           |
| `exclude_jobs` | `list[str]` | `[]`          | Job patterns to exclude           |

### Supported Events

- `SUCCESS`: Job completed successfully
- `FAILURE`: Job failed
- `CANCELED`: Job was canceled
- `RUNNING`: Job started running

### Job Filtering

Use wildcard patterns to control which jobs trigger notifications:

```python
config = AppriseNotificationsConfig(
    urls=["mailto://user:pass@gmail.com"],
    include_jobs=["prod_*", "critical_*"],  # Only production and critical jobs
    exclude_jobs=["*_test", "*_dev"],       # Exclude test and dev jobs
    events=["SUCCESS", "FAILURE"],
)
```

## Advanced Usage

### Op-level Notifications with Hooks

```python
from dagster_apprise import apprise_on_failure, apprise_on_success
import dagster as dg

@apprise_on_failure(urls=["mailto://user:pass@gmail.com"])
@dg.job
def critical_job():
    my_op()

# Or apply to specific ops
@dg.job
def selective_notifications():
    my_op.with_hooks({apprise_on_failure(urls=["mailto://user:pass@gmail.com"])})()
```

### Using AppriseResource in Ops

```python
import dagster as dg
from dagster_apprise import AppriseResource

@dg.op
def notify_op(apprise: AppriseResource):
    apprise.notify(title="Custom Alert", body="processing complete")
```

### Using with Environment Variables

```python
import os
from dagster_apprise import AppriseNotificationsConfig

# Load from environment
config = AppriseNotificationsConfig(
    urls=[os.getenv("GMAIL_URL")],
    base_url=os.getenv("DAGSTER_BASE_URL", "http://localhost:3000"),
    events=["SUCCESS", "FAILURE"],
)
```

### Multiple Notification Channels

```python
config = AppriseNotificationsConfig(
    urls=[
        "pover://user@token",  # Pushover for immediate testing alerts
        "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",  # Slack for team
        "mailto://user:pass@gmail.com",  # Email for backup
    ],
    events=["SUCCESS", "FAILURE"],
)
```

### Different Notifications for Different Jobs

```python
# Critical jobs - notify on all events
critical_config = AppriseNotificationsConfig(
    urls=["mailto://user:pass@gmail.com"],
    include_jobs=["critical_*"],
    events=["SUCCESS", "FAILURE", "CANCELED", "RUNNING"],
)

# Regular jobs - only notify on failures
regular_config = AppriseNotificationsConfig(
    urls=["https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"],
    include_jobs=["*"],
    exclude_jobs=["critical_*"],
    events=["FAILURE"],
)

# Combine both
defs = dg.Definitions(
    assets=[your_assets],
    jobs=[your_jobs],
    resources={
        **apprise_notifications(critical_config).resources,
        **apprise_notifications(regular_config).resources,
    },
    sensors=[
        *apprise_notifications(critical_config).sensors,
        *apprise_notifications(regular_config).sensors,
    ],
)
```

### Custom Run Failure Sensor

```python
from dagster_apprise import make_apprise_on_run_failure_sensor

apprise_on_failure = make_apprise_on_run_failure_sensor(
    urls=["mailto://user:pass@gmail.com"],
    monitored_jobs=["prod_*"]
)

defs = dg.Definitions(sensors=[apprise_on_failure])
```

### Integration with Dagster Logs

```python
@dg.op
def my_op(context):
    context.log.info("This appears in Dagster logs")
    error_condition = False
    if error_condition:
        context.resources.apprise.notify(
            title="Critical Error",
            body=f"Job {context.job_name} encountered an error",
        )
```

## About Apprise

**Apprise** is an open source notification library that allows users to easily send messages to dozens of providers without having to handle platform-specific implementation. See the details at the [project repository](https://github.com/caronc/apprise).
