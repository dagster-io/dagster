---
title: Databricks with Dagster Pipes
sidebar_position: 0
description: Use Dagster Pipes to orchestrate Databricks jobs with real-time log streaming and structured metadata reporting.
canonicalUrl: '/integrations/libraries/databricks/pipes'
slug: '/integrations/libraries/databricks/pipes'
---

You can run code in Databricks while streaming logs and structured metadata back to Dagster in real time with [Dagster Pipes](/integrations/external-pipelines). There are two approaches depending on your cluster type:

| Guide                                                                               | When to use                                                   |
| ----------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| [Serverless compute](/integrations/libraries/databricks/pipes/serverless-compute)   | Unity Catalog Volumes, serverless notebooks                   |
| [DBFS, classic clusters](/integrations/libraries/databricks/pipes/classic-clusters) | Python scripts on DBFS with classic (non-serverless) clusters |
