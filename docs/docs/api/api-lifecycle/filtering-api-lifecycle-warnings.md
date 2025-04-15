---
title: Filtering API lifecycle warnings
sidebar_position: 200
---

By default, Dagster logs warnings when APIs marked as preview, beta, superseded and deprecated are used in your code base. These warnings can be filtered out using the `warnings` module available by default in Python.

<CodeExample
    path="docs_snippets/docs_snippets/api/api_lifecycle/filtering_api_lifecycle_warnings.py"
    language="python"
/>

Note that Dagster uses the built-in `DeprecationWarning` for its deprecated APIs.