---
title: Observe
description: A suite of tools for end-to-end data platform observability in Dagster.
sidebar_class_name: hidden
canonicalUrl: '/guides/observe'
slug: '/guides/observe'
---

Dagster observability features focus on improving real-time understanding of data health, operational metrics, and historical trends, making it easier for you to monitor, troubleshoot, and explore your data workflows.

## Features

### Alerts (Dagster+)

Dagster+ alerts can notify you of critical events occurring in your deployment, such as [asset health status](/guides/observe/asset-health-status) changes or [freshness policy](/guides/observe/asset-freshness-policies) violations, so you can catch potential issues early, helping you resolve problems before they impact your stakeholders. For more information, see the [alerts guide](/guides/observe/alerts).

### Asset catalog (Dagster+)

The Dagster+ asset catalog displays assets broken out by compute kind, asset group, [code location](/deployment/code-locations), [tags](/guides/build/assets/metadata-and-tags/tags), owners, and more. You can also create flexible, shareable dashboards organized by asset, owner, tag, or business domain so every stakeholder can monitor performance and act with clarity. For more information, see the [asset catalog guide](/guides/observe/asset-catalog).

### Asset freshness policies

Ensure your most critical data stays fresh and trustworthy so teams can make timely, confident decisions without second-guessing the source. For more information, see the [freshness policies guide](/guides/observe/asset-freshness-policies).

### Asset health reporting (Dagster+)

Quickly identify which pipelines are running smoothly and which need attention with intuitive health indicators that highlight data quality and platform reliability in real time. For more information, see the [asset health status guide](/guides/observe/asset-health-status).

### Insights (Dagster+)

Unlock a comprehensive, dashboard-style view of your data platform’s health. Dagster+ Insights surfaces critical metrics, like success rate, freshness hit rate, and time to resolution for any selection of assets or jobs – all in real time. For more information, see the [Insights guide](/guides/observe/insights).
