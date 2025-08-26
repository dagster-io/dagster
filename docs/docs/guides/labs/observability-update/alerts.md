---
title: Asset health alerts and freshness alerts
description: TK
sidebar_position: 600
---

The [Dagster+ Summer Update](/guides/labs/observability-update) introduces two new ways to alert on the status of your assets: asset health alerts and freshness alerts.

:::info Enabling new alerts

To create and edit the new alerts, you will need to enable the "New homepage & observability UIs" user setting.

If you opt out of the new homepage and observability features, you will be unable to create new health or freshness alerts, or edit existing health or freshness alerts.

:::

## Health alerts

Asset health alerts send notifications when the overall health status of the asset changes:

![Create new health alery policy UI](/images/guides/labs/observability-update/create-new-alert-policy.png)

For more information on the meaning of the different health statuses, see the [asset health reporting documentation](/guides/labs/observability-update/asset-health#asset-health-statuses).

Health alerts differ from the existing event-based alerts, as they will only notify once when the health status of the asset changes, instead of every time an event occurs. For example, assume you have set up an asset health alert to notify when an asset becomes degraded. If the asset is healthy, and a run begins, and the asset fails to materialize, then the asset's health status is degraded, and Dagster will send you a health alert notification. If another run for the asset begins, and the asset fails to materialize, Dagster will not send a new notification, whereas an alert configured to notify on materialization failures would continue to send notifications. This makes the health status notifications more informative.

You cannot create an alert policy that notifies on both health status changes and on individual events (materialization failed).

## Freshness alerts

Asset freshness alerts send notifications when an asset's [freshness status](/guides/labs/observability-update/freshness) changes:

![Asset freshness alert in UI](/images/guides/labs/observability-update/create-new-freshness-alert.png)

For example, if you have an asset that you expect to materialize every six hours, you can create a [freshness policy](/guides/labs/observability-update/freshness) for the asset, and set up an alert to notify you when that policy is failing. If it's been six hours since the last materialization of the asset, you will receive a notification about the failing policy.
