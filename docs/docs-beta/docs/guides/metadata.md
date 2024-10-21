---
title: 'Adding tags and metadata to assets'
description: 'Learn how to add tags and metadata to assets to improve observability in Dagster'
sidebar_position: 40
sidebar_label: 'Add metadata'
---

Assets feature prominently in the Dagster UI. Attaching information to assets allows you to understand where they're stored, what they contain, and how they should be organized.

Using metadata in Dagster, you can:

- Attach ownership information
- Organize assets with tags
- Attach rich, complex information such as a Markdown description, a table schema, or a time series
- Link assets with their source code

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Familiarity with [Assets](/guides/data-assets)
</details>

## Adding owners to assets \{#owners}

In a large organization, it's important to know which individuals and teams are responsible for a given data asset:

<CodeExample filePath="guides/data-modeling/metadata/owners.py" language="python" />

`owners` must either be an email address or a team name prefixed by `team:`.

:::tip
With Dagster+ Pro, you can create asset-based alerts that automatically notify an asset's owners when triggered. Refer to the [Dagster+ alert documentation](/dagster-plus/deployment/alerts) for more information.
:::

## Organizing assets with tags \{#tags}

**Tags** are the primary way to organize assets in Dagster. You can attach several tags to an asset when it's defined, and they will appear in the UI. You can also use tags to search and filter for assets in the [Asset catalog](/todo). They're structured as key-value pairs of strings.

Here's an example of some tags you might apply to an asset:

```python
{"domain": "marketing", "pii": "true"}
```

Like `owners`, just pass a dictionary of tags to the `tags` argument when defining an asset:

<CodeExample filePath="guides/data-modeling/metadata/tags.py" language="python" />

Keep in mind that tags must contain only strings as keys and values. Additionally, the Dagster UI will render tags with the empty string as a "label" rather than a key-value pair.

## Attaching metadata to assets \{#attaching-metadata}

**Metadata** allows you to attach rich information to the asset, like a Markdown description, a table schema, or a time series. Metadata is more flexible than tags, as it can store more complex information.

Metadata can be attached to an asset at definition time, when the code is first imported, or at runtime when an asset is materialized.

### At definition time \{#definition-time-metadata}

Using definition metadata to describe assets can make it easy to provide context for you and your team. This metadata could be descriptions of the assets, the types of assets, or links to relevant documentation.

<CodeExample filePath="guides/data-modeling/metadata/definition-metadata.py" language="python" />

To learn more about the different types of metadata you can attach, see the [`MetadataValue`](/todo) API docs.

Some metadata keys will be given special treatment in the Dagster UI. See the [Standard metadata types](#standard-metadata-types) section for more information.

### At runtime \{#runtime-metadata}

With runtime metadata, you can surface information about an asset's materialization, such as how many records were processed or when the materialization occurred. This allows you to update an asset's information when it changes and track historical metadata as a time series.

<CodeExample filePath="guides/data-modeling/metadata/runtime-metadata.py" language="python" />

Numerical metadata is treated as a time series in the Dagster UI.

## Standard metadata types \{#standard-metadata-types}

The following metadata keys are given special treatment in the Dagster UI.

| Key                           | Description                                                                                                                                                                                                                                                                                                                                                     |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `dagster/uri`                 | **Type:** `str` <br/><br/> The URI for the asset, for example: "s3://my_bucket/my_object"                                                                                                                                                                                                                                                                               |
| `dagster/column_schema`       | **Type:** [`TableSchema`](/todo) <br/><br/> For an asset that's a table, the schema of the columns in the table. Refer to the [Table and column metadata](#table-schema) section for details.                                                                                                                                                      |
| `dagster/column_lineage`      | **Type:** [`TableColumnLineage`](/todo) <br/><br/> For an asset that's a table, the lineage of column inputs to column outputs for the table. Refer to the [Table and column metadata](#table-schema) section for details.                                                                                                                         |
| `dagster/row_count`           | **Type:** `int` <br/><br/> For an asset that's a table, the number of rows in the table. Refer to the Table metadata documentation for details.                                                                                                                                                                                                                 |
| `dagster/partition_row_count` | **Type:** `int` <br/><br/> For a partition of an asset that's a table, the number of rows in the partition.                                                                                                                                                                                                                                                     |
| `dagster/relation_identifier` | **Type:** `str` <br/><br/> A unique identifier for the table/view, typically fully qualified. For example, my_database.my_schema.my_table                                                                                                                                                                                                                       |
| `dagster/code_references`     | **Type:** [`CodeReferencesMetadataValue`](/todo) <br/><br/> A list of code references for the asset, such as file locations or references to GitHub URLs. Refer to the [Linking assets with their source code](#source-code) section for details. Should only be provided in definition-level metadata, not materialization metadata. |

## Table and column metadata \{#table-column}

Two of the most powerful metadata types are [`TableSchema`](/todo) and [`TableColumnLineage`](/todo). These metadata types allow stakeholders to view the schema of a table right within Dagster, and, in Dagster+, navigate the [Asset catalog](/todo) with the column lineage.

### Table schema metadata \{#table-schema}

The following example attaches table and column schema metadata at both definition time and runtime:

<CodeExample filePath="guides/data-modeling/metadata/table-schema-metadata.py" language="python" />

There are several data types and constraints available on [`TableColumn`](/todo) objects. Refer to the API documentation for more information.

### Column lineage metadata \{#column-lineage}

:::tip
Many integrations such as [dbt](https://docs.dagster.io/integrations/dbt/reference) automatically attach column lineage metadata out-of-the-box.
:::

Column lineage metadata is a powerful way to track how columns in a table are derived from other columns:

<CodeExample filePath="guides/data-modeling/metadata/table-column-lineage-metadata.py" language="python" title="Table column lineage metadata" />

:::tip
Dagster+ provides rich visualization and navigation of column lineage in the Asset catalog. Refer to the [Dagster+ documentation](/dagster-plus) for more information.
:::

## Linking assets with source code \{#source-code}

import Experimental from '../partials/\_Experimental.md';

<Experimental />

To link assets with their source code, you can attach a **code reference**. Code references are a type of metadata that allow you to easily view those assets' source code from the Dagster UI, both in local development and in production.

:::tip
Many integrations such as [dbt](https://docs.dagster.io/integrations/dbt/reference#attaching-code-reference-metadata) support this capability out of the box.
:::

### Attaching Python code references for local development \{#python-references}

Dagster can automatically attach code references to assets during local development with one line of code:

<CodeExample filePath="guides/data-modeling/metadata/python-local-references.py" language="python" />

### Customizing code references \{#custom-references}

If you want to customize how code references are attached - such as when you are building [domain-specific languages with asset factories](/guides/asset-factories) - you can manually add the `dagster/code_references` metadata to asset definitions:

<CodeExample filePath="guides/data-modeling/metadata/custom-local-references.py" language="python" />

### Attaching code references in production \{#production-references}

<Tabs>
  <TabItem value="dagster-plus" label="Dagster+">

Dagster+ can automatically annotate assets with code references to source control, such as GitHub or GitLab.

<CodeExample filePath="guides/data-modeling/metadata/plus-references.py" language="python" />

</TabItem>
<TabItem value="dagster-open-source" label="OSS">

If you aren't using Dagster+, you can annotate your assets with code references to source control, but it requires manual mapping:

<CodeExample filePath="guides/data-modeling/metadata/oss-references.py" language="python" />

`link_code_references_to_git` currently supports GitHub and GitLab repositories. It also supports customization of how file paths are mapped; see the `AnchorBasedFilePathMapping` API docs for more information.

</TabItem>
</Tabs>