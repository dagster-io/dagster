---
title: Dagster & Prometheus
sidebar_label: Prometheus
sidebar_position: 1
description: This integration allows you to push metrics to the Prometheus gateway from within a Dagster pipeline.
tags: [dagster-supported, monitoring]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-prometheus
pypi: https://pypi.org/project/dagster-prometheus
sidebar_custom_props:
  logo: images/integrations/prometheus.svg
partnerlink:
---

import Beta from '@site/docs/partials/\_Beta.md';

<Beta />

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-prometheus" />

## Example

<CodeExample path="docs_snippets/docs_snippets/integrations/prometheus.py" language="python" />

## About Prometheus

**Prometheus** is an open source systems monitoring and alerting toolkit. Originally built at SoundCloud, Prometheus joined the Cloud Native Computing Foundation in 2016 as the second hosted project, after Kubernetes.

Prometheus collects and stores metrics as time series data along with the timestamp at which it was recorded, alongside optional key-value pairs called labels.
