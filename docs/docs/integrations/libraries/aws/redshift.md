---
title: Dagster & AWS Redshift
sidebar_label: Redshift
sidebar_position: 8
description: Using this integration, you can connect to an AWS Redshift cluster and issue queries against it directly from your Dagster assets. This allows you to seamlessly integrate Redshift into your data pipelines, leveraging the power of Redshift's data warehousing capabilities within your Dagster workflows.
tags: [dagster-supported, storage]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-aws
pypi: https://pypi.org/project/dagster-aws/
sidebar_custom_props:
  logo: images/integrations/aws-redshift.svg
partnerlink: https://aws.amazon.com/
---

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-aws" />

## Examples

<CodeExample path="docs_snippets/docs_snippets/integrations/aws-redshift.py" language="python" />

## About AWS Redshift

**AWS Redshift** is a fully managed, petabyte-scale data warehouse service in the cloud. You can start with just a few hundred gigabytes of data and scale to a petabyte or more. This enables you to use your data to acquire new insights for your business and customers. Redshift offers fast query performance using SQL-based tools and business intelligence applications, making it a powerful tool for data warehousing and analytics.
