---
description: Create alert policies in Dagster+ via UI or dagster-cloud CLI on a per-deployment basis. Specify policy types, targets, and notification channels.
sidebar_position: 200
title: Creating alert policies in Dagster+
---

import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';

<DagsterPlus />

You can create alert policies in the Dagster+ UI or with the [`dagster-cloud` CLI](/deployment/dagster-plus/management/dagster-cloud-cli).

Alert policies are configured on a per-deployment basis. This means, for example, that asset alerts configured in a prod deployment are only applicable to assets in that deployment.

:::note

To send alert notifications through a channel other than email, you will need to [configure an alert notification service](/guides/monitor/alerts/configuring-an-alert-notification-service).

:::

## In the UI

1. In the Dagster UI, click **Deployment**.
2. In the left sidebar, click **Alert policies**.
3. Click **Create alert policy**.
4. Choose the [policy type](/guides/monitor/alerts/alert-policy-types) from the menu and click **Continue**.
5. Choose targets and events (if applicable) for your alert and click **Continue**.
6. Choose a notification channel for your alert and click **Continue**.
7. Review and save your alert and click **Save alert**.

## Using the CLI

1. Create an alert policy configuration file. For examples, see the [example configuration reference](/guides/monitor/alerts/example-config).
2. Sync the alert policy configuration file to your Dagster+ deployment:

```bash
dagster-cloud deployment alert-policies sync -a /path/to/alert_policies.yaml
```
