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
logo: /integrations/Prometheus.svg
categories:
  - Monitoring
enabledBy:
enables:
---

### About this integration

This integration allows you to push metrics to the Prometheus gateway from within a Dagster pipeline.

### Installation

```bash
pip install dagster-prometheus
```

### Example

```python
#import dagster as dg
from dagster_prometheus import PrometheusResource


@dg.asset
def prometheus_metric(prometheus: PrometheusResource):
    prometheus.push_to_gateway(job="my_job_label")


defs = dg.Definitions(
    assets=[prometheus_metric],
    resources={
        "prometheus": PrometheusResource(gateway="http://pushgateway.example.org:9091")
    },
)

```

### About Prometheus

**Prometheus** is an open source systems monitoring and alerting toolkit. Originally built at SoundCloud, Prometheus joined the Cloud Native Computing Foundation in 2016 as the second hosted project, after Kubernetes.

Prometheus collects and stores metrics as time series data along with the timestamp at which it was recorded, alongside optional key-value pairs called labels.
