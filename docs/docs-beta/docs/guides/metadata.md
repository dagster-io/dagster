---
title: 'Adding tags and metadata to assets'
description: 'Learn how to add tags and metadata to assets to improve observability in Dagster'
sidebar_position: 40
sidebar_label: 'Add metadata'
---

Assets feature prominently in the Dagster UI. It's often helpful to attach information to assets to understand where they're stored, what they contain, and how they should be organized.

In Dagster, you can attach ownership information, organize your assets with tags, attach rich, complex information with metadata, and link your assets with their source code.

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- A basic understanding of Dagster and assets. See the [Quick Start](/getting-started/quickstart) tutorial for an overview.
</details>

---

## Adding owners to your assets

In a large organization, it's important to know which individuals and teams are responsible for a given data asset:

<CodeExample filePath="guides/data-modeling/metadata/owners.py" language="python" title="Using owners" />

`owners` must either be an email address, or a team name prefixed by `team:`.

:::tip

With Dagster+ Pro, you can create asset-based alerts that will automatically notify an asset's owners when triggered. Refer to the [Dagster+ alert documentation](/dagster-plus/deployment/alerts) for more information.

:::

## Choosing between tags or metadata for custom information

In Dagster, you can attach custom information to assets in two ways: **tags** and **metadata**.

**Tags** are the primary way to organize assets in Dagster. You can attach several tags to an asset when it's defined, and they will appear in the UI. You can also use tags to search and filter for assets in the [Asset catalog](/todo). They're structured as key-value pairs of strings.

Here's an example of some tags you might apply to an asset:

```python
{"domain": "marketing", "pii": "true"}
```

**Metadata** allows you to attach rich information to the asset, like a Markdown description, a table schema, or a time series. Metadata is more flexible than tags, as it can store more complex information. Metadata can be attached to an asset at definition time (that's, when the code is first imported) or at runtime (every time an asset is materialized).

Here's an example of some metadata you might apply to an asset:

```python
{
    "link_to_docs": MetadataValue.url("https://..."),
    "snippet": MetadataValue.md("# Embedded markdown\n..."),
    "file_size_kb": MetadataValue.int(1024),
}
```

## Attaching tags to an asset

Like `owners`, just pass a dictionary of tags to the `tags` argument when defining an asset:

<CodeExample filePath="guides/data-modeling/metadata/tags.py" language="python" title="Using tags" />

Keep in mind that tags must contain only strings as keys and values. Additionally, the Dagster UI will render tags with the empty string as a "label" rather than a key-value pair.

## Attaching metadata to an asset at definition time

Attaching metadata at definition time is similar to how you attach tags.

<CodeExample filePath="guides/data-modeling/metadata/definition-metadata.py" language="python" title="Using metadata at definition time" />

To learn more about the different types of metadata you can attach, see the [`MetadataValue`](/todo) API docs.

Some metadata keys will be given special treatment in the Dagster UI. See the [Standard metadata types](#standard-metadata-types) section for more information.

## Attaching metadata to an asset at runtime

Metadata becomes powerful when it's attached when an asset is materialized. This allows you to update metadata when information about an asset changes and track historical metadata such as execution time and row counts as a time series.

<CodeExample filePath="guides/data-modeling/metadata/runtime-metadata.py" language="python" title="Using metadata at runtime" />

Any numerical metadata will be treated as a time series in the Dagster UI.

## Standard metadata types

Some metadata keys will be given special treatment in the Dagster UI.

| Key                           | Description                                                                                                                                                                                                                                                                                                                                                     |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `dagster/uri`                 | **Type:** `str` <br/><br/> The URI for the asset, for example: "s3://my_bucket/my_object"                                                                                                                                                                                                                                                                               |
| `dagster/column_schema`       | **Type:** [`TableSchema`](/todo) <br/><br/> For an asset that's a table, the schema of the columns in the table. Refer to the [Table and column metadata](#table-and-column-metadata) section for details.                                                                                                                                                      |
| `dagster/column_lineage`      | **Type:** [`TableColumnLineage`](/todo) <br/><br/> For an asset that's a table, the lineage of column inputs to column outputs for the table. Refer to the [Table and column metadata](#table-and-column-metadata) section for details.                                                                                                                         |
| `dagster/row_count`           | **Type:** `int` <br/><br/> For an asset that's a table, the number of rows in the table. Refer to the Table metadata documentation for details.                                                                                                                                                                                                                 |
| `dagster/partition_row_count` | **Type:** `int` <br/><br/> For a partition of an asset that's a table, the number of rows in the partition.                                                                                                                                                                                                                                                     |
| `dagster/relation_identifier` | **Type:** `str` <br/><br/> A unique identifier for the table/view, typically fully qualified. For example, my_database.my_schema.my_table                                                                                                                                                                                                                       |
| `dagster/code_references`     | **Type:** [`CodeReferencesMetadataValue`](/todo) <br/><br/> A list of code references for the asset, such as file locations or references to GitHub URLs. Refer to the [Linking assets with their source code](#linking-assets-with-their-source-code) section for details. Should only be provided in definition-level metadata, not materialization metadata. |

## Table and column metadata

Two of the most powerful metadata types are [`TableSchema`](/todo) and [`TableColumnLineage`](/todo). These metadata types allow stakeholders to view the schema of a table right within Dagster, and, in Dagster+, navigate the [Asset catalog](/todo) with the column lineage.

### Table schema metadata

Here's a quick example of how to attach this metadata at both definition time and runtime:

<CodeExample filePath="guides/data-modeling/metadata/table-schema-metadata.py" language="python" title="Table schema metadata" />

There are several data types and constraints available on [`TableColumn`](/todo) objects. Refer to the API documentation for more information.)

### Column lineage metadata

:::tip

Many integrations such as [dbt](https://docs.dagster.io/integrations/dbt/reference) automatically attach this metadata out-of-the-box.

:::

Column lineage metadata is a powerful way to track how columns in a table are derived from other columns. Here is how you can manually attach this metadata:

<CodeExample filePath="guides/data-modeling/metadata/table-column-lineage-metadata.py" language="python" title="Table column lineage metadata" />

:::tip

Dagster+ provides rich visualization and navigation of column lineage in the Asset catalog. Refer to the [Dagster+ documentation](/dagster-plus) for more information.

:::

## Linking assets with their source code

:::warning

This feature is considered experimental and is under active development. This guide will be updated as we roll out new features.

:::

Attaching code reference metadata to your Dagster asset definitions allows you to easily view those assets' source code from the Dagster UI both in local development and in production.

> Many integrations such as [dbt](https://docs.dagster.io/integrations/dbt/reference#attaching-code-reference-metadata) support this capability out of the box. Refer to the integration documentation for more information.

### Attaching Python code references for local development

Dagster can automatically attach code references to your assets during local development with one line of code.

<CodeExample filePath="guides/data-modeling/metadata/python-local-references.py" language="python" title="Local source code references" />

### Customizing code references

If you want to customize how code references are attached - such as when you are building [domain-specific languages with asset factories](/guides/asset-factories) - you can manually add the `dagster/code_references` metadata to your asset definitions.

<CodeExample filePath="guides/data-modeling/metadata/custom-local-references.py" language="python" title="Custom local source code references" />

### Attaching code references in production

<Tabs>
  <TabItem value="dagster-plus" label="Dagster+">

Dagster+ can automatically annotate your assets with code references to source control such as GitHub or GitLab.

<CodeExample filePath="guides/data-modeling/metadata/plus-references.py" language="python" title="Production source code references (Dagster+)" />

</TabItem>
<TabItem value="dagster-open-source" label="OSS">

If you aren't using Dagster+, you can annotate your assets with code references to source control, but it requires a little more manual mapping.

<CodeExample filePath="guides/data-modeling/metadata/oss-references.py" language="python" title="Production source code references (OSS)" />

[`link_code_references_to_git`](/todo) currently supports GitHub and GitLab repositories. It also supports customization of how file paths are mapped; see the [`AnchorBasedFilePathMapping`](/todo) API docs for more information.

</TabItem>
</Tabs>
