---
title: 'Dagster+ Observability update'
description: An upcoming suite of tools for end-to-end data platform observability
sidebar_position: 100
---

:::info

These features are under active development, and are in limited early access. You may encounter feature gaps, and the functionality and APIs may change. Sign up to join the early access program [here](https://dagster.io/summer). To report issues or give feedback, please reach out to your Customer Success Manager.

:::

The Dagster+ Summer Update is a collection of new functionality that marks a major leap forward in observability and orchestration for data platforms. It focuses on improving real-time understanding of data health, operational metrics, and historical trends. With a redesigned user experience, the update makes it easier for teams to monitor, troubleshoot, and explore their data workflows.

### How to join and enable the beta

The full suite of new features is available in limited early access for Dagster+ users. Sign up to join the early access program [here](https://dagster.io/summer).

Once you are a member of the early access program, you can enable or disable the new experiences in your user settings, via the "New health & observability UIs" setting.

## Features

### New homepage

Get a holistic view of your data platform’s health from the moment you log in. The redesigned Dagster+ homepage keeps your most important signals front and center so you can track key metrics in real time, surface issues quickly, and stay focused on what matters most.

### Freshness policies

Ensure your most critical data stays fresh and trustworthy so teams can make timely, confident decisions without second-guessing the source. For more information, see the [Freshness policies guide](/guides/labs/observability-update/freshness).

### Asset health reporting

Quickly identify which datasets are performing well and which need attention with intuitive health indicators that highlight data quality and platform reliability in real time. For more information, see the [Asset health reporting guide](/guides/labs/observability-update/asset-health).

### Real-time Insights

Unlock a comprehensive, dashboard-style view of your data platform’s health. The new Insights experience surfaces critical metrics, like success rate, freshness hit rate, and time to resolution for any selection of assets or jobs – all in real time. For more information, see the [Real-time insights guide](/guides/labs/observability-update/insights).

### Custom catalog dashboards

Give teams a focused view of the data that matters most. Create flexible, shareable dashboards organized by asset, owner, tag, or business domain so every stakeholder can monitor performance and act with clarity.

### Asset facets

With asset facets, you can customize asset views to surface the most relevant metadata, like ownership, health, freshness, and automation signals.

To configure asset facets, click the facet configuration button on the asset lineage page:

![Asset facets configuration button](/images/guides/labs/observability-update/asset-facets-config-button.png)

Next, select the facets you want to display:

![Asset facets configuration modal](/images/guides/labs/observability-update/asset-facets-config-modal.png)

:::note

Asset facets are only configured for your view. Changing the facet configuration will not change it for other users of your data platform.

:::
