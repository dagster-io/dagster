---
description: Filter Dagster API lifecycle warnings using the Python warnings module.
sidebar_position: 200
title: Filtering API lifecycle warnings
---

By default, Dagster logs warnings when APIs marked as preview, beta, superseded and deprecated are used in your code base. These warnings can be filtered out using the `warnings` module available by default in Python.

<CodeExample
  path="docs_snippets/docs_snippets/api/api_lifecycle/filtering_api_lifecycle_warnings.py"
  language="python"
/>

Note that Dagster uses the built-in `DeprecationWarning` for its deprecated APIs.
