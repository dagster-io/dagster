---
title: "Dagster Pipes subprocess reference"
description: "This page shows ways to execute external code with Dagster Pipes with different entities in the Dagster system."
---

This reference shows usage of Dagster Pipes with other entities in the Dagster system. For a step-by-step walkthrough, refer to the [Dagster Pipes tutorial](/guides/build/external-pipelines/using-dagster-pipes).

## Specifying environment variables and extras

When launching the subprocess, you may want to make environment variables or additional parameters available in the external process. Extras are arbitrary, user-defined parameters made available on the context object in the external process.

<Tabs>
<TabItem value="External code in external_code.py">

In the external code, you can access extras via the `PipesContext` object:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/subprocess/with_extras_env/external_code.py" lineStart="2" />

</TabItem>
<TabItem value="Dagster code in dagster_code.py">

The `run` method to the `PipesSubprocessClient` resource also accepts `env` and `extras` , which allow you to specify environment variables and extra arguments when executing the subprocess:

Note: We're using `os.environ` in this example, but Dagster's recommendation is to use <PyObject section="resources" module="dagster" object="EnvVar" /> in production.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/subprocess/with_extras_env/dagster_code.py" />

</TabItem>
</Tabs>

## Working with @asset_check

Sometimes, you may not want to materialize an asset, but instead want to report a data quality check result. When your asset has data quality checks defined in <PyObject section="asset-checks" module="dagster" object="asset_check" decorator />:

<Tabs>

<TabItem value="External code in external_code.py">

From the external code, you can report to Dagster that an asset check has been performed via <PyObject section="libraries" module="dagster_pipes" object="PipesContext" method="report_asset_check" />. Note that `asset_key` in this case is required, and must match the asset key defined in <PyObject section="asset-checks" module="dagster" object="asset_check" decorator />:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/subprocess/with_asset_check/external_code.py" />

</TabItem>
<TabItem value="Dagster code in dagster_code.py">

On Dagster's side, the `PipesClientCompletedInvocation` object returned from `PipesSubprocessClient` includes a `get_asset_check_result` method, which you can use to access the <PyObject section="asset-checks" module="dagster" object="AssetCheckResult" /> event reported by the subprocess.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/subprocess/with_asset_check/dagster_code.py" />

</TabItem>
</Tabs>

## Working with multi-assets

Sometimes, you may invoke a single call to an API that results in multiple tables being updated, or you may have a single script that computes multiple assets. In these cases, you can use Dagster Pipes to report back on multiple assets at once.

<Tabs>

<TabItem value="External code in external_code.py">

**Note**: When working with multi-assets, <PyObject section="libraries" module="dagster_pipes" object="PipesContext" method="report_asset_materialization" /> may only be called once per unique asset key. If called more than once, an error similar to the following will surface:

```bash
Calling {method} with asset key {asset_key} is undefined. Asset has already been materialized, so no additional data can be reported for it
```

Instead, you’ll need to set the `asset_key` parameter for each instance of <PyObject module="dagster_pipes" section="libraries" object="PipesContext" method="report_asset_materialization" />:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/subprocess/with_multi_asset/external_code.py" />

</TabItem>

<TabItem value="Dagster code in dagster_code.py">

In the Dagster code, you can use <PyObject section="assets" module="dagster" object="multi_asset" decorator /> to define a single asset that represents multiple assets. The `PipesClientCompletedInvocation` object returned from `PipesSubprocessClient` includes a `get_results` method, which you can use to access all the events, such as multiple <PyObject section="ops" module="dagster" object="AssetMaterialization" pluralize /> and <PyObject section="asset-checks" module="dagster" object="AssetCheckResult" pluralize />, reported by the subprocess:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/subprocess/with_multi_asset/dagster_code.py" />

</TabItem>
</Tabs>

## Passing custom data

Sometimes, you may want to pass data back from the external process for use in the orchestration code for purposes other than reporting directly to Dagster such as use in creating an output. In this example we use custom messages to create an I/O managed output that is returned from the asset.

<Tabs>
<TabItem value="External code in external_code.py">

In the external code, we send messages using `report_custom_message`. The message can be any data that is JSON serializable.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/subprocess/custom_messages/external_code.py" />

</TabItem>
<TabItem value="Dagster code in dagster_code.py">

In the Dagster code we receive custom messages using `get_custom_messages`.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/subprocess/custom_messages/dagster_code.py" />

</TabItem>
</Tabs>

## Passing rich metadata to Dagster

Dagster supports rich metadata types such as <PyObject section="metadata" module="dagster" object="TableMetadataValue"/>, <PyObject section="metadata" module="dagster" object="UrlMetadataValue"/>, and <PyObject section="metadata" module="dagster" object="JsonMetadataValue"/>. However, because the `dagster-pipes` package doesn't have a direct dependency on `dagster`, you'll need to pass a raw dictionary back to Dagster with a specific format. For a given metadata type, you will need to specify a dictionary with the following keys:

- `type`: The type of metadata value, such as `table`, `url`, or `json`.
- `raw_value`: The actual value of the metadata.

Below are examples of specifying data for all supported metadata types. Float, integer, boolean, string, and null metadata objects can be passed directly without the need for a dictionary.

### Examples for complex metadata types

#### URL Metadata

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/subprocess/rich_metadata/url_metadata.py" />

#### Path Metadata

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/subprocess/rich_metadata/path_metadata.py" />

#### Notebook Metadata

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/subprocess/rich_metadata/notebook_metadata.py" />

#### JSON Metadata

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/subprocess/rich_metadata/json_metadata.py" />

#### Markdown Metadata

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/subprocess/rich_metadata/markdown_metadata.py" />

#### Table Metadata

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/subprocess/rich_metadata/table_metadata.py" />

#### Table Schema Metadata

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/subprocess/rich_metadata/table_schema_metadata.py" />

#### Table Column Lineage Metadata

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/subprocess/rich_metadata/table_column_lineage.py" startAfter="start_table_column_lineage" endBefore="end_table_column_lineage" />

#### Timestamp Metadata

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/subprocess/rich_metadata/timestamp_metadata.py" startAfter="start_timestamp" endBefore="end_timestamp" />
