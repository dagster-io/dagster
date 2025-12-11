---
title: Dagster &  Azure Data Lake Storage Gen 2
sidebar_label: Azure
sidebar_position: 1
description: Dagster helps you use Azure Storage Accounts as part of your data pipeline. Azure Data Lake Storage Gen 2 (ADLS2) is our primary focus but we also provide utilities for Azure Blob Storage.
tags: [dagster-supported, storage]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-azure
pypi: https://pypi.org/project/dagster-azure/
sidebar_custom_props:
  logo: images/integrations/azure.svg
canonicalUrl: '/integrations/libraries/azure'
slug: '/integrations/libraries/azure'
---

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-azure" />

## Example

<CodeExample path="docs_snippets/docs_snippets/integrations/azure-adls2.py" language="python" />

In this updated code, we use `ADLS2Resource` directly instead of `adls2_resource`. The configuration is passed to `ADLS2Resource` during its instantiation.

## About Azure Data Lake Storage Gen 2 (ADLS2)

**Azure Data Lake Storage Gen 2 (ADLS2)** is a set of capabilities dedicated to big data analytics, built on Azure Blob Storage. ADLS2 combines the scalability, cost-effectiveness, security, and rich capabilities of Azure Blob Storage with a high-performance file system that's built for analytics and is compatible with the Hadoop Distributed File System (HDFS). This makes it an ideal choice for data lakes and big data analytics.
