---
title: "Asset metadata"
---

[Assets](/guides/build/assets/) feature prominently in the Dagster UI. Attaching information to assets allows you to understand where they're stored, what they contain, and how they should be organized.

Using metadata in Dagster, you can:

- Attach ownership information
- Organize assets with tags
- Attach rich, complex information such as a Markdown description, a table schema, or a time series
- Link assets with their source code

## Adding owners to assets \{#owners}

In a large organization, it's important to know which individuals and teams are responsible for a given data asset.

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/data-modeling/metadata/owners.py" language="python" />

:::note

`owners` must either be an email address or a team name prefixed by `team:` (e.g. `team:data-eng`).

:::

:::tip
With Dagster+ Pro, you can create asset-based alerts that automatically notify an asset's owners when triggered. Refer to the [Dagster+ alert documentation](/dagster-plus/features/alerts) for more information.
:::

## Organizing assets with tags \{#tags}

[**Tags**](tags) are the primary way to organize assets in Dagster. You can attach several tags to an asset when it's defined, and they will appear in the UI. You can also use tags to search and filter for assets in the Asset catalog. They're structured as key-value pairs of strings.

Here's an example of some tags you might apply to an asset:

```python
{"domain": "marketing", "pii": "true"}
```

As with `owners`, you can pass a dictionary of tags to the `tags` argument when defining an asset:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/data-modeling/metadata/tags.py" language="python" />

Keep in mind that tags must contain only strings as keys and values. Additionally, the Dagster UI will render tags with the empty string as a "label" rather than a key-value pair.

## Attaching metadata to assets \{#attaching-metadata}

**Metadata** allows you to attach rich information to the asset, like a Markdown description, a table schema, or a time series. Metadata is more flexible than tags, as it can store more complex information.

Metadata can be attached to an asset at definition time, when the code is first imported, or at runtime when an asset is materialized.

### At definition time \{#definition-time-metadata}

Using definition metadata to describe assets can make it easy to provide context for you and your team. This metadata could be descriptions of the assets, the types of assets, or links to relevant documentation.

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/data-modeling/metadata/definition-metadata.py" language="python" />

To learn more about the different types of metadata you can attach, see the <PyObject section="metadata" module="dagster" object="MetadataValue" /> API docs.

Some metadata keys will be given special treatment in the Dagster UI. See the [Standard metadata types](#standard-metadata-types) section for more information.

### At runtime \{#runtime-metadata}

With runtime metadata, you can surface information about an asset's materialization, such as how many records were processed or when the materialization occurred. This allows you to update an asset's information when it changes and track historical metadata as a time series.

To attach materialization metadata to an asset, returning a <PyObject section="assets" module="dagster" object="MaterializeResult" /> object containing a `metadata` parameter. This parameter accepts a dictionary of key/value pairs, where keys must be a string.

When specifying values, use the <PyObject section="metadata" module="dagster" object="MetadataValue" /> utility class to wrap the data to ensure it displays correctly in the UI. Values can also be primitive Python types, which Dagster will convert to the appropriate `MetadataValue`.

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/data-modeling/metadata/runtime-metadata.py" language="python" />

:::note

Numerical metadata is treated as a time series in the Dagster UI.

:::

## Standard metadata types \{#standard-metadata-types}

The following metadata keys are given special treatment in the Dagster UI.

| Key                           | Description                                                                                                                                                                                                                                                                                                                                                     |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `dagster/uri`                 | **Type:** `str` <br/><br/> The URI for the asset, for example: "s3://my_bucket/my_object"                                                                                                                                                                                                                                                                               |
| `dagster/column_schema`       | **Type:** <PyObject section="metadata" module="dagster" object="TableSchema" /> <br/><br/> For an asset that's a table, the schema of the columns in the table. Refer to the [Table and column metadata](#table-column) section for details.                                                                                                                                                      |
| `dagster/column_lineage`      | **Type:** <PyObject section="metadata" module="dagster" object="TableColumnLineage" /><br/><br/> For an asset that's a table, the lineage of column inputs to column outputs for the table. Refer to the [Table and column metadata](#table-column) section for details.                                                                                                                         |
| `dagster/row_count`           | **Type:** `int` <br/><br/> For an asset that's a table, the number of rows in the table. Refer to the Table metadata documentation for details.                                                                                                                                                                                                                 |
| `dagster/partition_row_count` | **Type:** `int` <br/><br/> For a partition of an asset that's a table, the number of rows in the partition.                                                                                                                                                                                                                                                     |
| `dagster/table_name`          | **Type:** `str` <br/><br/> A unique identifier for the table/view, typically fully qualified. For example, my_database.my_schema.my_table                                                                                                                                                                                                                       |
| `dagster/code_references`     | **Type:** <PyObject section="metadata" module="dagster" object="CodeReferencesMetadataValue" /><br/><br/> A list of [code references](#source-code) for the asset, such as file locations or references to GitHub URLs. Should only be provided in definition-level metadata, not materialization metadata. |

## Table and column metadata \{#table-column}

Two of the most powerful metadata types are <PyObject section="metadata" module="dagster" object="TableSchema" /> and <PyObject section="metadata" module="dagster" object="TableColumnLineage" />. These metadata types allow stakeholders to view the schema of a table right within Dagster, and, in Dagster+, navigate to the [Asset catalog](/dagster-plus/features/asset-catalog/) with the column lineage.

### Table schema metadata \{#table-schema}

The following example attaches [table and column schema metadata](table-metadata) at both definition time and runtime:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/data-modeling/metadata/table-schema-metadata.py" language="python" />

There are several data types and constraints available on <PyObject section="metadata" module="dagster" object="TableColumn" /> objects. For more information, see the API documentation.

### Column lineage metadata \{#column-lineage}

:::tip
Many integrations such as [dbt](/integrations/libraries/dbt/) automatically attach column lineage metadata out-of-the-box.
:::

[Column lineage metadata](column-level-lineage) is a powerful way to track how columns in a table are derived from other columns:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/data-modeling/metadata/table-column-lineage-metadata.py" language="python" title="Table column lineage metadata" />

:::tip
Dagster+ provides rich visualization and navigation of column lineage in the Asset catalog. Refer to the [Dagster+ documentation](/dagster-plus/features/asset-catalog/) for more information.
:::

## Linking assets with source code \{#source-code}

import Beta from '../../../../partials/\_Beta.md';

<Beta />


To link assets with their source code, you can attach a code reference. Code references are a type of metadata that allow you to easily view those assets' source code from the Dagster UI, both in local development and in production.

:::tip

Many integrations, such as [dbt](/integrations/libraries/dbt/reference#attaching-code-reference-metadata), support this capability.

:::

### Attaching Python code references for local development \{#python-references}

Dagster can automatically attach code references to assets during local development:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/data-modeling/metadata/python-local-references.py" language="python" />

### Customizing code references \{#custom-references}

If you want to customize how code references are attached - such as when you are building [domain-specific languages with asset factories](/guides/build/assets/creating-asset-factories) - you can manually add the `dagster/code_references` metadata to asset definitions:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/data-modeling/metadata/custom-local-references.py" language="python" />

### Attaching code references in production \{#production-references}

<Tabs>
  <TabItem value="dagster-plus" label="Dagster+">

Dagster+ can automatically annotate assets with code references to source control, such as GitHub or GitLab.

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/data-modeling/metadata/plus-references.py" language="python" />

</TabItem>
<TabItem value="dagster-open-source" label="OSS">

If you aren't using Dagster+, you can annotate your assets with code references to source control, but it requires manual mapping:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/data-modeling/metadata/oss-references.py" language="python" />

`link_code_references_to_git` currently supports GitHub and GitLab repositories. It also supports customization of how file paths are mapped; see the `AnchorBasedFilePathMapping` API docs for more information.

</TabItem>
</Tabs>
