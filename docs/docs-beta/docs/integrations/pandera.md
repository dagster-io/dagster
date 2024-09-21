---
layout: Integration
status: published
name: Pandera
title: Dagster & Pandera
sidebar_label: Pandera
excerpt: Generate Dagster Types from Pandera dataframe schemas.
date: 2022-11-07
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-pandera
docslink: https://docs.dagster.io/integrations/pandera
partnerlink: https://pandera.readthedocs.io/en/stable/
logo: /integrations/Pandera.svg
categories:
  - Metadata
enabledBy:
enables:
---

### About this integration

The `dagster-pandera` integration library provides an API for generating Dagster Types from [Pandera DataFrame schemas](https://pandera.readthedocs.io/en/stable/dataframe_schemas.html).

Like all Dagster types, Dagster-Pandera-generated types can be used to annotate op inputs and outputs. This provides runtime type-checking with rich error reporting and allows Dagster UI to display information about a DataFrame's structure.

### Installation

```bash
pip install dagster-pandera
```

### Example

<CodeExample filePath="integrations/pandera.py" language="python" />

### About Pandera

**Pandera** is a statistical data testing toolkit, and a data validation library for scientists, engineers, and analysts seeking correctness.
