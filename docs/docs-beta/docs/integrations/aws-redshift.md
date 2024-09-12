---
layout: Integration
status: published
name: AWS Redshift
title: Dagster & AWS Redshift
sidebar_label: AWS Redshift
excerpt: "Using this integration, you can seamlessly integrate AWS Redshift into your Dagster workflows, leveraging Redshifts data warehousing capabilities for your data pipelines."
date: 2024-06-21
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-aws
docslink: 
partnerlink: https://aws.amazon.com/
logo: /integrations/aws-redshift.svg
categories:
  - Storage
enabledBy:
enables:
---

### About this integration

Using this integration, you can connect to an AWS Redshift cluster and issue queries against it directly from your Dagster assets. This allows you to seamlessly integrate Redshift into your data pipelines, leveraging the power of Redshift's data warehousing capabilities within your Dagster workflows.

### Installation

```bash
pip install dagster-aws
```

### Examples

```python
from dagster import Definitions, asset, EnvVar
from dagster_aws.redshift import RedshiftClientResource


@asset
def example_redshift_asset(context, redshift: RedshiftClientResource):
    result = redshift.get_client().execute_query("SELECT 1", fetch_results=True)
    context.log.info(f"Query result: {result}")


redshift_configured = RedshiftClientResource(
    host="my-redshift-cluster.us-east-1.redshift.amazonaws.com",
    port=5439,
    user="dagster",
    password=EnvVar("DAGSTER_REDSHIFT_PASSWORD"),
    database="dev",
)

defs = Definitions(
    assets=[example_redshift_asset],
    resources={"redshift": redshift_configured},
)
```

### About AWS Redshift

**AWS Redshift** is a fully managed, petabyte-scale data warehouse service in the cloud. You can start with just a few hundred gigabytes of data and scale to a petabyte or more. This enables you to use your data to acquire new insights for your business and customers. Redshift offers fast query performance using SQL-based tools and business intelligence applications, making it a powerful tool for data warehousing and analytics.
