---
layout: Integration
status: published
name: GCS
title: Dagster & GCP GCS
sidebar_label: GCS
excerpt: Integrate with GCP GCS.
date: 2022-11-07
apireflink: https://docs.dagster.io/api/python-api/libraries/dagster-gcp
docslink: https://docs.dagster.io/integrations/libraries/gcp/gcs
partnerlink: https://cloud.google.com/storage
categories:
  - Storage
enabledBy:
enables:
tags: [dagster-supported, storage]
sidebar_custom_props:
  logo: images/integrations/gcp-gcs.svg
---

This integration allows you to interact with Google Cloud Storage (GCS) using Dagster. It provides resources, I/O Managers, and utilities to manage and store data in GCS, making it easier to integrate GCS into your data pipelines.

### Installation

```bash
pip install dagster-gcp
```

### Examples

<CodeExample path="docs_beta_snippets/docs_beta_snippets/integrations/gcp-gcs.py" language="python" />

### About Google Cloud Platform GCS

**Google Cloud Storage (GCS)**, is a scalable and secure object storage service. GCS is designed for storing and accessing any amount of data at any time, making it ideal for data science, AI infrastructure, and frameworks for ML like AutoML. With this integration, you can leverage GCS for efficient data storage and retrieval within your Dagster pipelines.
