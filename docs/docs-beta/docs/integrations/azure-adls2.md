---
layout: Integration
status: published
name: Azure Data Lake Storage Gen 2 (ADLS2)
title: Dagster &  Azure Data Lake Storage Gen 2 (ADLS2)
sidebar_label: Azure Data Lake Storage Gen 2 (ADLS2)
excerpt: Get utilities for ADLS2 and Blob Storage.
date: 2022-11-07
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-azure
docslink:
partnerlink: https://azure.microsoft.com/
logo: /integrations/Azure.svg
categories:
  - Storage
enabledBy:
enables:
---

### About this integration

Dagster helps you use Azure Storage Accounts as part of your data pipeline. Azure Data Lake Storage Gen 2 (ADLS2) is our primary focus but we also provide utilities for Azure Blob Storage.

### Installation

```bash
pip install dagster-azure
```

### Examples

<CodeExample filePath="integrations/azure-adls2.py" language="python" />

In this updated code, we use `ADLS2Resource` directly instead of `adls2_resource`. The configuration is passed to `ADLS2Resource` during its instantiation.

### About Azure Data Lake Storage Gen 2 (ADLS2)

**Azure Data Lake Storage Gen 2 (ADLS2)** is a set of capabilities dedicated to big data analytics, built on Azure Blob Storage. ADLS2 combines the scalability, cost-effectiveness, security, and rich capabilities of Azure Blob Storage with a high-performance file system that's built for analytics and is compatible with the Hadoop Distributed File System (HDFS). This makes it an ideal choice for data lakes and big data analytics.
