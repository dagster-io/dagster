---
layout: Integration
status: published
title: Dagster &  Azure Data Lake Storage Gen 2
sidebar_label: Azure Data Lake Storage Gen 2
excerpt: Get utilities for ADLS2 and Blob Storage.
date: 2022-11-07
apireflink: https://docs.dagster.io/api/python-api/libraries/dagster-azure
docslink:
partnerlink: https://azure.microsoft.com/
logo: /integrations/Azure.svg
categories:
  - Storage
enabledBy:
enables:
tags: [dagster-supported, storage]
sidebar_custom_props: 
  logo: images/integrations/azure.svg
---

Dagster helps you use Azure Storage Accounts as part of your data pipeline. Azure Data Lake Storage Gen 2 (ADLS2) is our primary focus but we also provide utilities for Azure Blob Storage.

### Installation

```bash
pip install dagster-azure
```

### Example

<CodeExample path="docs_beta_snippets/docs_beta_snippets/integrations/azure-adls2.py" language="python" />

In this updated code, we use `ADLS2Resource` directly instead of `adls2_resource`. The configuration is passed to `ADLS2Resource` during its instantiation.

### About Azure Data Lake Storage Gen 2 (ADLS2)

**Azure Data Lake Storage Gen 2 (ADLS2)** is a set of capabilities dedicated to big data analytics, built on Azure Blob Storage. ADLS2 combines the scalability, cost-effectiveness, security, and rich capabilities of Azure Blob Storage with a high-performance file system that's built for analytics and is compatible with the Hadoop Distributed File System (HDFS). This makes it an ideal choice for data lakes and big data analytics.
