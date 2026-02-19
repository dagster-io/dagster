---
title: Dagster & GCP GCS
sidebar_label: GCS
sidebar_position: 5
description: This integration allows you to interact with Google Cloud Storage (GCS) using Dagster. It provides resources, I/O Managers, and utilities to manage and store data in GCS, making it easier to integrate GCS into your data pipelines.
tags: [dagster-supported, storage]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-gcp
pypi: https://pypi.org/project/dagster-gcp/
sidebar_custom_props:
  logo: images/integrations/gcp-gcs.svg
partnerlink: https://cloud.google.com/storage
---

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-gcp" />

## Examples

<CodeExample path="docs_snippets/docs_snippets/integrations/gcp-gcs.py" language="python" />

## About Google Cloud Platform GCS

**Google Cloud Storage (GCS)**, is a scalable and secure object storage service. GCS is designed for storing and accessing any amount of data at any time, making it ideal for data science, AI infrastructure, and frameworks for ML like AutoML. With this integration, you can leverage GCS for efficient data storage and retrieval within your Dagster pipelines.
