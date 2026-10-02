---
title: "Groups"
description: Every Dagster asset belongs to a group. Group names can use `/` separators to define a hierarchy, which the UI renders as nested groups in the asset graph.
sidebar_position: 500
---

Groups are the most basic way to organize assets in Dagster.

## Assigning a group

Assets belong to the `default` group unless you set the `group_name` argument:

<CodeExample path="docs_snippets/docs_snippets/guides/build/assets/metadata/groups.py" language="python" startAfter="start_flat" endBefore="end_flat" />

`group_name` is accepted anywhere an asset is defined or modified, including <PyObject section="assets" module="dagster" object="AssetSpec" />, the `group_name` argument to `load_assets_from_modules`, the attributes of a [`defs.yaml` file](/guides/build/assets/metadata-and-tags/adding-attributes-to-assets), and integration translators such as the [dbt translator's `get_group_name`](/integrations/libraries/dbt/reference#customizing-group-names).

An asset can belong to only one group. To organize assets along several dimensions at once, use [tags](/guides/build/assets/metadata-and-tags/tags) instead.

## Nested groups

A group name can contain `/` separators to place the group inside a hierarchy. Parent groups are implied by their children — you don't need to declare `marketing` for `marketing/paid` to exist:

<CodeExample path="docs_snippets/docs_snippets/guides/build/assets/metadata/groups.py" language="python" startAfter="start_nested" endBefore="end_nested" />

:::note

Nested group names require Dagster 1.13.9 or later.

:::

## Groups in the UI

Groups can be used to organize the representation of assets in your asset graph. Each group is drawn as a labeled box around its assets, and a nested group is drawn as a box inside its parent's box. Clicking a group's header collapses it into a single node showing rolled-up status counts for everything inside, including any nested groups; clicking that node expands it again. The sidebar renders the same hierarchy as an expandable tree.
