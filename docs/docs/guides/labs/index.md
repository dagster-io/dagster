---
description: Dagster Labs features are in preview and under active development.
sidebar_class_name: hidden
title: Labs
canonicalUrl: '/guides/labs'
slug: '/guides/labs'
---

The features in this section are under active development. You may encounter feature gaps, and the APIs may change.

### Compass AI assistant (Dagster+)

Compass analyzes run logs, identifies root causes of failures, and suggests debugging steps. Trigger a summary from any completed run or from a degraded asset on the home page, then ask follow-up questions in a conversational chat interface. For more information, see the [Compass AI assistant guide](/guides/labs/compass-ai-assistant).

### Connections

Connections allow you to easily discover and sync data warehouse assets from sources like Snowflake, BigQuery, Postgres, and Databricks into Dagster. These assets are viewable in the Dagster UI catalog, and you can set alerts on schema changes or metadata values (like row count). For more information, see the [Connections docs](/guides/labs/connections).

### Webhook alert notifications (Dagster+)

Dagster+ alerts can be configured to send HTTP requests to any endpoint when an alert is triggered, enabling deep integration with chat clients, task management tools, incident management software, or custom internal systems. For more information, see the [Webhook alert notification docs](/guides/labs/webhook-alerts).
