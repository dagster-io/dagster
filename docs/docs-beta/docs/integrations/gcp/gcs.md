---
layout: Integration
status: published
name: GCS
title: Dagster & GCP GCS
sidebar_label: GCS
excerpt: Integrate with GCP GCS.
date: 2022-11-07
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-gcp
docslink:
partnerlink:
logo: /integrations/gcp-gcs.svg
categories:
  - Storage
enabledBy:
enables:
---

### About this integration

This integration allows you to interact with Google Cloud Storage (GCS) using Dagster. It provides resources, I/O Managers, and utilities to manage and store data in GCS, making it easier to integrate GCS into your data pipelines.

### Installation

```bash
pip install dagster-gcp
```

### Examples

<CodeExample filePath="integrations/gcp-gcs.py" language="python" />

### About Google Cloud Platform GCS

**Google Cloud Storage (GCS)**, is a scalable and secure object storage service. GCS is designed for storing and accessing any amount of data at any time, making it ideal for data science, AI infrastructure, and frameworks for ML like AutoML. With this integration, you can leverage GCS for efficient data storage and retrieval within your Dagster pipelines.
