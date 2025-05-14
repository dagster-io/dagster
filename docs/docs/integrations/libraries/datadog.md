---
title: Dagster & Datadog
sidebar_label: Datadog
description: While Dagster provides comprehensive monitoring and observability of the pipelines it orchestrates, many teams look to centralize all their monitoring across apps, processes and infrastructure using Datadog's 'Cloud Monitoring as a Service'. The Datadog integration allows you to publish metrics to Datadog from within Dagster ops.
tags: [dagster-supported, monitoring]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-datadog
pypi: https://pypi.org/project/dagster-datadog/
sidebar_custom_props:
  logo: images/integrations/datadog.svg
partnerlink: https://www.datadoghq.com/
---

import Beta from '@site/docs/partials/\_Beta.md';

<Beta />

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-datadog" />

## Example

<CodeExample path="docs_snippets/docs_snippets/integrations/datadog.py" language="python" />

## About Datadog

**Datadog** is an observability service for cloud-scale applications, providing monitoring of servers, databases, tools, and services, through a SaaS-based data analytics platform.
