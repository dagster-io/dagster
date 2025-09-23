---
description: Use the Dagster+ asset catalog to view assets, access the global asset lineage, build dasbhoards, reload definitions, and search assets by asset key, compute kind, asset group, code location, and more.
title: Asset catalog (Dagster+)
sidebar_position: 100
tags: [dagster-plus-feature]
canonicalUrl: '/guides/observe/asset-catalog'
slug: '/guides/observe/asset-catalog'
---

import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';

<DagsterPlus />

:::note

This guide covers the updated asset catalog. For documentation on legacy asset catalog features, including catalog views, see the [legacy guide](https://release-1-11-10.archive.dagster-docs.io/guides/build/assets/asset-catalog).

:::

The Dagster+ asset catalog displays assets broken out by compute kind, asset group, [code location](/deployment/code-locations), [tags](/guides/build/assets/metadata-and-tags/tags), owners, and more. On this page, you can:

- View all assets in your Dagster deployment
- Search assets by asset key, compute kind, asset group, code location, tags, owners, and more
- [Create dashboards from asset selections](/guides/observe/asset-catalog/dashboards)
- Access the global asset lineage
- Reload definitions

To access the asset catalog, click **Catalog** in the left sidebar.

![The Asset catalog page in the Dagster UI](/images/guides/observe/asset-catalog/dagster-plus-asset-catalog.png)

:::note

By default, assets without definitions are not shown in the asset catalog. These are typically historical assets that have been removed from your definitions. You can choose to see these assets in user settings by toggling "Show assets without definitions in catalog."

:::
