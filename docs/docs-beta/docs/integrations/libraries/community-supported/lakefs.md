---
layout: Integration
status: published
name: LakeFS
title: Dagster & LakeFS
sidebar_label: LakeFS
excerpt: lakeFS provides version control and complete lineage over the data lake.
date: 2023-06-27
communityIntegration: true
apireflink: https://pydocs.lakefs.io/
docslink:
partnerlink: https://lakefs.io/
logo: /integrations/lakefs.svg
categories:
  - Storage
enabledBy:
enables:
---

### About this integration

By integrating with lakeFS, a big data scale version control system, you can leverage the versioning capabilities of lakeFS to track changes to your data. This integration allows you to have a complete lineage of your data, from the initial raw data to the transformed and processed data, making it easier to understand and reproduce data transformations.

With lakeFS and Dagster integration, you can ensure that data flowing through your Dagster jobs is easily reproducible. lakeFS provides a consistent view of your data across different versions, allowing you to troubleshoot pipeline runs and ensure consistent results.

Furthermore, with lakeFS branching capabilities, Dagster jobs can run on separate branches without additional storage costs, creating isolation and allowing promotion of only high-quality data to production leveraging a CI/CD pipeline for your data.

### Installation

```bash
pip install lakefs-client
```

### Example

<CodeExample filePath="integrations/lakefs.py" language="python" />

### About lakeFS

**lakeFS** is on a mission to simplify the lives of data engineers, data scientists and analysts providing a data version control platform at scale.
