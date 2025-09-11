---
title: Asset freshness alerts
description: Dagster+ asset freshness alerts keep you informed about the freshness of your assets in Dagster+.
tags: [dagster-plus-feature]
---

import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';

<DagsterPlus />

:::info Enabling new alerts

To create and edit the new alerts, you will need to enable the "New homepage & observability UIs" user setting. Note that if you opt out of the new homepage and observability features, you will be unable to create new health or freshness alerts, or edit existing health or freshness alerts.

:::

Asset freshness alerts send notifications when an asset's [freshness status](/guides/observe/asset-freshness-policies) changes:

![Asset freshness alert in UI](/images/guides/observe/create-new-freshness-alert.png)

For example, if you have an asset that you expect to materialize every six hours, you can create a [freshness policy](/guides/observe/asset-freshness-policies) for the asset, and set up an alert to notify you when that policy is failing. If it's been six hours since the last materialization of the asset, you will receive a notification about the failing policy.
