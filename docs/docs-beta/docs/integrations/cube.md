---
layout: Integration
status: published
name: Cube
title: Dagster & Cube
sidebar_label: Cube
excerpt: 'Push changes from upstream data sources to Cubes semantic layer.'
date: 2023-08-30
apireflink: https://cube.dev/docs/orchestration-api/dagster
partnerlink: https://cube.dev/
communityIntegration: true
logo: /integrations/cube.svg
categories:
  - Other
enabledBy:
enables:
---

### About this integration

With the `dagster_cube` integration you can setup Cube and Dagster to work together so that Dagster can push changes from upstream data sources to Cube using its integration API.

### Installation

```bash
pip install dagster_cube
```

### Example

<CodeExample filePath="integrations/cube.py" language="python" />

### About Cube

**Cube.js** is the semantic layer for building data applications. It helps data engineers and application developers access data from modern data stores, organize it into consistent definitions, and deliver it to every application.
