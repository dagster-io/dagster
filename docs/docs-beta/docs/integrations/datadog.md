---
layout: Integration
status: published
name: Datadog
title: Dagster & Datadog
sidebar_label: Datadog
excerpt: Publish metrics to Datadog from within Dagster ops and entralize your monitoring metrics.
date: 2022-11-07
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-datadog
docslink:
partnerlink: https://www.datadoghq.com/
logo: /integrations/Datadog.svg
categories:
  - Monitoring
enabledBy:
enables:
---

### About this integration

While Dagster provides comprehensive monitoring and observability of the pipelines it orchestrates, many teams look to centralize all their monitoring across apps, processes and infrastructure using Datadog's 'Cloud Monitoring as a Service'. The `dagster-datadog` integration allows you to publish metrics to Datadog from within Dagster ops.

### Installation

```bash
pip install dagster-datadog
```

### Example

<CodeExample filePath="integrations/datadog.py" language="python" />

### About Datadog

**Datadog** is an observability service for cloud-scale applications, providing monitoring of servers, databases, tools, and services, through a SaaS-based data analytics platform.
