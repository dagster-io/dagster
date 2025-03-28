---
title: "Column-level lineage"
description: "Column lineage enables data and analytics engineers alike to understand how a column is created and used in your data platform."
sidebar_position: 4000
---

# Column-level lineage

For assets that produce database tables, column-level lineage can be a powerful tool for improving collaboration and debugging issues. Column lineage enables data and analytics engineers alike to understand how a column is created and used in your data platform.

## How it works

Emitted as materialization metadata, column lineage can be:

- Specified on assets defined in Dagster
- Enabled for assets loaded from integrations like dbt

Dagster uses this metadata to display the column's upstream and downstream dependencies, accessible via the asset's details page in the Dagster UI. **Note**: Viewing column-level lineage in the UI is a Dagster+ feature.

## Enabling column-level lineage

### For assets defined in Dagster

To enable column-level lineage on Dagster assets that produce database tables, you'll need to:

1. Return a <PyObject section="assets" module="dagster" object="MaterializeResult" /> object containing a `metadata` parameter
2. In `metadata`, use the `dagster/column_lineage` key to create a <PyObject section="metadata" module="dagster" object="TableColumnLineage" /> object
3. In this object, use <PyObject section="metadata" module="dagster" object="TableColumnLineage" displayText="TableColumnLineage.deps_by_column" /> to define a list of columns
4. For each column, use <PyObject section="metadata" module="dagster" object="TableColumnDep" /> to define its dependencies. This object accepts `asset_key` and `column_name` arguments, allow you to specify the name of the asset and column that make up the dependency.

Let's take a look at an example:

<CodeExample path="docs_snippets/docs_snippets/concepts/metadata-tags/asset_column_lineage.py" />

When materialized, the `my_asset` asset will create two columns: `new_column_foo` and `new_column_qux`.

The `new_column_foo` column is dependent on two other columns:

1. `column_bar` from the `source_bar` asset
2. `column_baz` from the `source_baz` asset

And the second column, `new_column_qux` has is dependent on `column_quuz` from the `source_bar` asset.

If using Dagster+, you can view the column-level lineage in the Dagster UI.

### For assets loaded from integrations

Column-level lineage is currently supported for the dbt integration. Refer to the [dbt documentation](/integrations/libraries/dbt/reference) for more information.

## Viewing column-level lineage in the Dagster UI

:::note

Viewing column lineage in the UI is a Dagster+ feature.

:::

1. In the Dagster UI, open the **Asset details** page for an asset with column-level lineage enabled.
2. Navigate to the **Overview** tab if it isn't already open.
3. In the **Columns** section, click the **branch** icon in the row of the column you want to view. The icon is on the far right side of the row:

    ![Highlighted column lineage icon in the Asset details page of the Dagster UI](/images/guides/build/assets/metadata-tags/column-lineage-icon.png)

The graph will display the column's column dependencies, grouped by asset:

![Column lineage for a credit_utilization column in the Dagster UI](/images/guides/build/assets/metadata-tags/column-level-lineage.png)

To view another column's lineage, click the **Column** dropdown and select another column.
