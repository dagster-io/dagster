---
title: Dagster & GCP BigQuery
sidebar_label: BigQuery
description: Integrate with GCP BigQuery.
tags: [dagster-supported, storage]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-gcp
pypi: https://pypi.org/project/dagster-gcp/
sidebar_custom_props:
  logo: images/integrations/gcp-bigquery.svg
partnerlink: https://cloud.google.com/bigquery
canonicalUrl: '/integrations/libraries/gcp/bigquery'
slug: '/integrations/libraries/gcp/bigquery'
---

import Beta from '@site/docs/partials/\_Beta.md';

<Beta />

The Google Cloud Platform BigQuery integration allows data engineers to easily query and store data in the BigQuery data warehouse through the use of the `BigQueryResource`.

### Installation

<PackageInstallInstructions packageName="dagster-gcp" />

### Examples

<CodeExample path="docs_snippets/docs_snippets/integrations/gcp-bigquery.py" language="python" />

### About Google Cloud Platform BigQuery

The Google Cloud Platform BigQuery service, offers a fully managed enterprise data warehouse that enables fast SQL queries using the processing power of Google's infrastructure.
