---
description: Create alert policies in Dagster+ via UI or dagster-cloud CLI on a per-deployment basis. Specify policy types, targets, and notification channels.
sidebar_position: 200
tags: [dagster-plus-feature]
title: Creating alert policies
---

import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';

<DagsterPlus />

You can create alert policies in the Dagster+ UI or with the [`dagster-cloud` CLI](/api/clis/dagster-cloud-cli).

Alert policies are configured on a per-deployment basis. This means, for example, that asset alerts configured in a prod deployment are only applicable to assets in that deployment.

:::note

To send alert notifications through a channel other than email, you will need to [configure an alert notification service](/guides/observe/alerts/configuring-an-alert-notification-service).

:::

## In the UI

1. In the Dagster+ UI, in the left sidebar, click **Deployment**.
2. In the top nav, click **Alert policies**.
3. Click **Create alert policy**.
4. Choose the [policy type](/guides/observe/alerts/alert-policy-types) from the menu and click **Continue**.
5. Choose targets and events (if applicable) for your alert.
   - **Health status change** will notify when overall health status has changed.
   - **Specific events** will notify on materialization success or failure, asset check status, or freshness policy passing, warning, or failure, depending on configuration.
6. Click **Continue**.
7. Choose a notification channel for your alert and click **Continue**.
8. Review your alert and click **Save alert**.

:::info

You cannot create an alert policy that notifies on both health status changes and on individual events (such as materialization failure).

:::

## Using the CLI

1. Create an alert policy configuration file. For examples, see the [example configuration reference](/guides/observe/alerts/example-config).
2. Sync the alert policy configuration file to your Dagster+ deployment:

```bash
dagster-cloud deployment alert-policies sync -a /path/to/alert_policies.yaml
```
