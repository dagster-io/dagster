---
title: Databricks with Dagster Pipes
sidebar_position: 0
description: Use Dagster Pipes to orchestrate Databricks jobs with real-time log streaming and structured metadata reporting.
canonicalUrl: '/integrations/libraries/databricks/pipes'
slug: '/integrations/libraries/databricks/pipes'
---

You can run code in Databricks while streaming logs and structured metadata back to Dagster in real time with [Dagster Pipes](/integrations/external-pipelines). Choose a guide based on your cluster type, or on whether the job already exists in Databricks:

| Guide                                                                               | When to use                                                   |
| ----------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| [Serverless compute](/integrations/libraries/databricks/pipes/serverless-compute)   | Unity Catalog Volumes, serverless notebooks                   |
| [DBFS, classic clusters](/integrations/libraries/databricks/pipes/classic-clusters) | Python scripts on DBFS with classic (non-serverless) clusters |
| [Existing jobs (workflows)](/integrations/libraries/databricks/pipes/existing-jobs) | Jobs already defined in Databricks, triggered by job ID       |
