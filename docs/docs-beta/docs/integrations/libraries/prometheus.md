---
layout: Integration
status: published
name: Prometheus
title: Dagster & Prometheus
sidebar_label: Prometheus
excerpt: Integrate with Prometheus via the prometheus_client library.
date: 2024-08-30
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-prometheus
docslink: https://prometheus.io/
partnerlink:
categories:
  - Monitoring
enabledBy:
enables:
tags: [dagster-supported, monitoring]
sidebar_custom_props:
  logo: images/integrations/prometheus.svg
---

This integration allows you to push metrics to the Prometheus gateway from within a Dagster pipeline.

### Installation

```bash
pip install dagster-prometheus
```

### Example

<CodeExample path="docs_beta_snippets/docs_beta_snippets/integrations/prometheus.py" language="python" />

### About Prometheus

**Prometheus** is an open source systems monitoring and alerting toolkit. Originally built at SoundCloud, Prometheus joined the Cloud Native Computing Foundation in 2016 as the second hosted project, after Kubernetes.

Prometheus collects and stores metrics as time series data along with the timestamp at which it was recorded, alongside optional key-value pairs called labels.
