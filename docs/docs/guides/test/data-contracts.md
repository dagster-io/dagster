---
description: Data contracts define agreements about the structure, format, and quality of data using asset checks to ensure consistency and reliability across your data pipeline.
sidebar_position: 600
title: Data contracts with asset checks
---

Data contracts define agreements about the structure, format, and quality of data, ensuring consistency and reliability across your data pipeline. Without formal contracts, schema changes such as renamed columns, type changes, or missing fields can cause failures in downstream systems. These issues are often discovered too late, leading to broken pipelines and unreliable data.

In Dagster, you can implement data contracts using [asset checks](/guides/test/asset-checks) that validate the actual schema against a predefined contract specification.

## Getting started

To implement data contracts using asset checks, follow these general steps:

1. **Define your assets with schema metadata**: Configure assets to automatically extract and attach column schema metadata
2. **Create a contract specification**: Define the expected schema, types, and validation rules in a YAML file
3. **Define an asset check**: Create an asset check that validates the actual schema against the contract
4. **Pass the asset check to the `Definitions` object**: Asset checks must be added to `Definitions` for Dagster to recognize them
5. **View validation results in the UI**: Contract validation results will appear in the UI when the check runs

## Defining assets with schema metadata

<CodeExample
  path="docs_snippets/docs_snippets/guides/data-assets/quality-testing/data-contracts/assets.py"
  language="python"
  title="src/<project_name>/defs/assets.py"
  startAfter="start_asset"
  endBefore="end_asset"
/>

The `shipments` asset uses `create_table_schema_metadata_from_dataframe` from `dagster-pandas` to automatically extract and attach column schema metadata. This metadata becomes available for validation by asset checks without requiring manual schema specification.

## Defining the contract specification

The data contract is defined in a separate YAML file, making it easy to version control and collaborate across teams:

<CodeExample
  path="docs_snippets/docs_snippets/guides/data-assets/quality-testing/data-contracts/shipments_contract.yaml"
  language="yaml"
  title="src/<project_name>/defs/shipments_contract.yaml"
/>

The contract defines expected column names and types, field descriptions, required columns, and includes a version number for tracking changes over time.

## Implementing contract validation

An asset check validates the actual asset schema against the data contract:

<CodeExample
  path="docs_snippets/docs_snippets/guides/data-assets/quality-testing/data-contracts/assets.py"
  language="python"
  title="src/<project_name>/defs/asset_checks.py"
  startAfter="start_asset_check"
  endBefore="end_asset_check"
/>

The validation process loads the data contract from the YAML file, retrieves the actual schema from the asset's metadata, and compares them to identify type mismatches, missing required columns, and unexpected extra columns. When violations are detected, the check returns detailed results with specific information about each issue.

This approach provides early detection of schema violations, catching issues immediately when assets are materialized rather than waiting for downstream failures. The external YAML contracts serve as explicit documentation that can be version controlled alongside code, facilitating team collaboration and providing a clear communication tool between data producers and consumers.

## Viewing contract validation results

When the data contract asset check runs, the results will appear in the Dagster UI. Successful validations indicate that the asset schema matches the contract, while failures provide detailed information about specific violations:

![Asset check status](/images/guides/tests/catalog_asset_check.png)

## Next steps

- Learn more about [asset checks](/guides/test/asset-checks)
- Explore [unit testing assets and ops](/guides/test/unit-testing-assets-and-ops)
