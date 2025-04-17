---
title: Dagster & Cube
sidebar_label: Cube
description: Push changes from upstream data sources to Cubes semantic layer.
tags: []
source:
pypi: https://pypi.org/project/dagster-cube/
built_by: Community
sidebar_custom_props:
  logo: images/integrations/cube.svg
  community: true
partnerlink: https://cube.dev/
---

With the `dagster_cube` integration you can setup Cube and Dagster to work together so that Dagster can push changes from upstream data sources to Cube using its integration API.

### Installation

```bash
pip install dagster_cube
```

### Example

<CodeExample path="docs_snippets/docs_snippets/integrations/cube.py" language="python" />

### About Cube

**Cube.js** is the semantic layer for building data applications. It helps data engineers and application developers access data from modern data stores, organize it into consistent definitions, and deliver it to every application.
