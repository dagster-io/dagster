---
layout: Integration
status: published
name: Pandas
title: Dagster & Pandas
sidebar_label: Pandas
excerpt: Implement validation on pandas DataFrames.
date: 2022-11-07
apireflink: https://docs.dagster.io/api/python-api/libraries/dagster-pandas
docslink: https://docs.dagster.io/integrations/libraries/pandas/
partnerlink: https://pandas.pydata.org/
categories:
  - Metadata
enabledBy:
enables:
tags: [dagster-supported, metadata]
sidebar_custom_props:
  logo: images/integrations/pandas.svg
---

import Beta from '../../../partials/\_Beta.md';

<Beta />

Perform data validation, emit summary statistics, and enable reliable DataFrame serialization/deserialization. The dagster_pandas library provides you with the utilities for implementing validation on Pandas DataFrames. The Dagster type system generates documentation of your DataFrame constraints and makes it accessible in the Dagster UI.

### Installation

```bash
pip install dagster-pandas
```

### About Pandas

**Pandas** is a popular Python package that provides data structures designed to make working with "relational" or "labeled" data both easy and intuitive. Pandas aims to be the fundamental high-level building block for doing practical, real-world data analysis in Python.
