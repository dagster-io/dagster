---
title: Alerts
description: 
sidebar_position: 600
---

The Dagster+ Summer Update introduces two new ways to alert on the status of your assets: asset health alerts and freshness alerts. These alerts can only be created and edited by users who have enable the "New health & observability UIs" user setting. (TODO - confirm name of setting)

## Health alerts

Asset health alerts work by sending notifications when the overall health status of the asset changes.

You cannot create an alert policy that notifies on health status changes and on individual events (materialization failed).

### Health states

You can create an alert that notifies on any of the health state changes described below:

| State | Description |
|-------|-------------|
| Healthy | TK |
| Warning | TK |
| Degraded | TK |

### Example

If you want to know when an asset becomes degraded, you can set up an asset health alert to notify you when that happens. If the asset is healthy, and a run begins, and the asset fails to materialize, then the asset's health status is degraded, and Dagster will send you a health alert notification.

:::note

Health alerts are different from from existing alerts in that notifications will not be sent if events occur that keep the asset in its current health state. In the example above, if the asset checks for the asset fail after the health alert notification is sent, you will not receive an additional health alert notification, since the asset's health status is still degraded.

:::

## Freshness alerts




:::note

If you opt out of the new homepage and observability features, you will be unable to create new health or freshness alerts, or edit existing health or freshness alerts.

:::

