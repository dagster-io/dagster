---
layout: Integration
status: published
name: Dataproc
title: Dagster & GCP Dataproc
sidebar_label: Dataproc
excerpt: Integrate with GCP Dataproc.
date: 2022-11-07
apireflink: https://docs.dagster.io/api/python-api/libraries/dagster-gcp
docslink: https://docs.dagster.io/integrations/libraries/gcp/dataproc
partnerlink: https://cloud.google.com/dataproc
categories:
  - Compute
enabledBy:
enables:
tags: [dagster-supported, compute]
sidebar_custom_props:
  logo: images/integrations/gcp-dataproc.svg
---

import Beta from '../../../partials/\_Beta.md';

<Beta />

Using this integration, you can manage and interact with Google Cloud Platform's Dataproc service directly from Dagster. This integration allows you to create, manage, and delete Dataproc clusters, and submit and monitor jobs on these clusters.

### Installation

```bash
pip install dagster-gcp
```

### Examples

<CodeExample path="docs_beta_snippets/docs_beta_snippets/integrations/gcp-dataproc.py" language="python" />

### About Google Cloud Platform Dataproc

Google Cloud Platform's **Dataproc** is a fully managed and highly scalable service for running Apache Spark, Apache Hadoop, and other open source data processing frameworks. Dataproc simplifies the process of setting up and managing clusters, allowing you to focus on your data processing tasks without worrying about the underlying infrastructure. With Dataproc, you can quickly create clusters, submit jobs, and monitor their progress, all while benefiting from the scalability and reliability of Google Cloud Platform.
