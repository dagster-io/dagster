---
title: Dagster & Datadog
sidebar_label: Datadog
sidebar_position: 1
description: While Dagster provides comprehensive monitoring and observability of the pipelines it orchestrates, many teams look to centralize all their monitoring across apps, processes and infrastructure using Datadog's 'Cloud Monitoring as a Service'. The Datadog integration allows you to publish metrics to Datadog from within Dagster ops.
tags: [dagster-supported, monitoring]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-datadog
pypi: https://pypi.org/project/dagster-datadog/
sidebar_custom_props:
  logo: images/integrations/datadog.svg
partnerlink: https://www.datadoghq.com/
canonicalUrl: '/integrations/libraries/datadog'
slug: '/integrations/libraries/datadog'
---

import Beta from '@site/docs/partials/\_Beta.md';

<Beta />

<p>{frontMatter.description}</p>

:::tip[No-code Datadog integration]

Datadog's new Dagster integration streams event logs to Datadog and includes an out-of-the-box log pipeline and dashboard. In Datadog, navigate to the Dagster integration tile and click Connect Accounts to launch the OAuth flow. Within 10 minutes, the Dagster Overview dashboard starts showing new log events, provided there are any active Dagster jobs emitting events. Get started in [Datadog](https://app.datadoghq.com/account/login) or learn more in their [docs](https://docs.datadoghq.com/integrations/dagster-plus/).

:::

## Installation

<PackageInstallInstructions packageName="dagster-datadog" />

## Example

<CodeExample path="docs_snippets/docs_snippets/integrations/datadog.py" language="python" />

## About Datadog

**Datadog** is an observability service for cloud-scale applications, providing monitoring of servers, databases, tools, and services, through a SaaS-based data analytics platform.
