---
title: Asset health alerts and freshness alerts
description: Asset health alerts and freshness alerts keep you informed about the status of your assets.
tags: [dagster-plus]
sidebar_position: 600
---

The [Dagster+ Summer Update](/guides/labs/observability-update) introduces two new ways to alert on the status of your assets: asset health alerts and freshness alerts.

## Enabling new alerts

To create and edit the new alerts, you will need to enable the "New homepage & observability UIs" user setting. Note that if you opt out of the new homepage and observability features, you will be unable to create new health or freshness alerts, or edit existing health or freshness alerts.

## Health alerts

Asset health alerts send notifications when the overall [health status](/guides/labs/observability-update/asset-health) of the asset changes:

![Create new health alert policy UI](/images/guides/labs/observability-update/create-new-alert-policy.png)

To make health alert notifications as relevant as possible, they only notify once when the health status of the asset changes, instead of every time an event occurs. This makes them different from the existing event-based alerts.

For example, assume you have set up an asset health alert to notify when an asset becomes degraded. If the asset is healthy, but fails to materialize after a run begins, then the asset's health status is degraded, and you will receive a health alert notification. If another run for the asset begins, and the asset again fails to materialize, you will not receive a new notification. (An alert configured to notify on materialization failures would continue to send notifications in this case.)

:::info

You cannot create an alert policy that notifies on both health status changes and on individual events (such as materialization failure).

:::

## Freshness alerts

Asset freshness alerts send notifications when an asset's [freshness status](/guides/labs/observability-update/freshness) changes:

![Asset freshness alert in UI](/images/guides/labs/observability-update/create-new-freshness-alert.png)

For example, if you have an asset that you expect to materialize every six hours, you can create a [freshness policy](/guides/labs/observability-update/freshness) for the asset, and set up an alert to notify you when that policy is failing. If it's been six hours since the last materialization of the asset, you will receive a notification about the failing policy.
