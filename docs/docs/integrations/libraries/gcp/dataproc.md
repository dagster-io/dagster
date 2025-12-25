---
title: Dagster & GCP Dataproc
sidebar_label: Dataproc
sidebar_position: 4
description: Using this integration, you can manage and interact with Google Cloud Platform's Dataproc service directly from Dagster. This integration allows you to create, manage, and delete Dataproc clusters, and submit and monitor jobs on these clusters.
tags: [dagster-supported, compute]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-gcp
pypi: https://pypi.org/project/dagster-gcp/
sidebar_custom_props:
  logo: images/integrations/gcp-dataproc.svg
partnerlink: https://cloud.google.com/dataproc
---

import Beta from '@site/docs/partials/\_Beta.md';

<Beta />

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-gcp" />

## Examples

<CodeExample path="docs_snippets/docs_snippets/integrations/gcp-dataproc.py" language="python" />

## About Google Cloud Platform Dataproc

Google Cloud Platform's **Dataproc** is a fully managed and highly scalable service for running Apache Spark, Apache Hadoop, and other open source data processing frameworks. Dataproc simplifies the process of setting up and managing clusters, allowing you to focus on your data processing tasks without worrying about the underlying infrastructure. With Dataproc, you can quickly create clusters, submit jobs, and monitor their progress, all while benefiting from the scalability and reliability of Google Cloud Platform.
