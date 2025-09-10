---
title: Asset health alerts (Dagster+)
description: Asset health alerts keep you informed about the overall health status of your assets in Dagster+.
tags: [dagster-plus-feature]
sidebar_position: 200
---

import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';

<DagsterPlus />

In Dagster+, you can configure alerts on the status of your assets with asset health alerts and freshness alerts.

:::info Enabling new alerts

To create and edit the new alerts, you will need to enable the "New homepage & observability UIs" user setting. Note that if you opt out of the new homepage and observability features, you will be unable to create new health or freshness alerts, or edit existing health or freshness alerts.

:::

Asset health alerts send notifications when the overall [health status](/guides/observe/asset-health/reporting) of the asset changes:

![Create new health alert policy UI](/images/guides/observe/create-new-alert-policy.png)

To make health alert notifications as relevant as possible, they only notify once when the health status of the asset changes, instead of every time an event occurs. This makes them different from the existing event-based alerts.

For example, assume you have set up an asset health alert to notify when an asset becomes degraded. If the asset is healthy, but fails to materialize after a run begins, then the asset's health status is degraded, and you will receive a health alert notification. If another run for the asset begins, and the asset again fails to materialize, you will not receive a new notification. (An alert configured to notify on materialization failures would continue to send notifications in this case.)

:::info

You cannot create an alert policy that notifies on both health status changes and on individual events (such as materialization failure).

:::
