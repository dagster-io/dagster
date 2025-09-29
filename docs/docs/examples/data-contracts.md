---
title: Data contracts
description: How to implement and validate data contracts using asset checks.
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/dagster-primary-mark.svg
  miniProject: true
tags: [mini-project]
---

In this example, we'll explore how to implement data contracts in Dagster using [asset checks](/guides/test/asset-checks). Data contracts define agreements about the structure, format, and quality of data, ensuring consistency and reliability across your data pipeline.

### Problem: Managing schema changes and data quality

Imagine you have a `shipments` asset that produces data consumed by multiple downstream assets and processes. Without formal contracts, schema changes—such as renamed columns, type changes, or missing fields—can cause failures in downstream systems. These issues are often discovered too late, leading to broken pipelines and unreliable data.

### Solution: Formal data contracts with automated validation

This approach implements data contracts using three components: an asset that automatically captures schema metadata, an external YAML contract specification, and an asset check that validates the actual schema against the contract.

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/data_contracts/assets.py"
  language="python"
  title="src/project_mini/defs/data_contracts/assets.py"
  startAfter="start_asset"
  endBefore="end_asset"
/>

The `shipments` asset uses `create_table_schema_metadata_from_dataframe` from `dagster-pandas` to automatically extract and attach column schema metadata. This metadata becomes available for validation by asset checks without requiring manual schema specification.

### Contract specification

The data contract is defined in a separate YAML file, making it easy to version control and collaborate across teams:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/data_contracts/shipments_contract.yaml"
  language="yaml"
  title="src/project_mini/defs/data_contracts/shipments_contract.yaml"
/>

The contract defines expected column names and types, field descriptions, required columns, and includes a version number for tracking changes over time.

### Automated validation

An asset check validates the actual asset schema against the data contract:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/data_contracts/assets.py"
  language="python"
  title="src/project_mini/defs/data_contracts/asset_checks.py"
  startAfter="start_asset_check"
  endBefore="end_asset_check"
/>

The validation process loads the data contract from the YAML file, retrieves the actual schema from the asset's metadata, and compares them to identify type mismatches, missing required columns, and unexpected extra columns. When violations are detected, the check returns detailed results with specific information about each issue.

This approach provides early detection of schema violations, catching issues immediately when assets are materialized rather than waiting for downstream failures. The external YAML contracts serve as explicit documentation that can be version controlled alongside code, facilitating team collaboration and providing a clear communication tool between data producers and consumers.

![2048 resolution](/images/examples/data-contracts/catalog_asset_check.png)
