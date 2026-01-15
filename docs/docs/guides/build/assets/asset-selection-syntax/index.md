---
description: The Dagster asset selection syntax allows you to query assets within your data lineage graph by selecting upstream and downstream layers of the graph, and using filters to narrow your selection, and functions to return the root or sink assets of a given selection. 
sidebar_position: 1000
title: Asset selection
canonicalUrl: "/guides/build/assets/asset-selection-syntax"
slug: "/guides/build/assets/asset-selection-syntax"
---

Dagster's asset selection syntax allows you to query and view assets within your data lineage graph. You can select upstream and downstream layers of the graph, use filters to narrow down your selection, and use functions to return the root or sink assets of a given selection.

With asset selection, you can:

- Select a set of assets to view in the Dagster UI
- Define a job in Python that targets a selection of assets
- List or materialize a set of assets using the [Dagster CLI](/api/clis/cli#dagster-asset)

## Availability

In the **Dagster OSS UI**, the asset selection syntax is available on:

- The asset catalog
- The global asset lineage page

In the **Dagster+ UI**, the asset selection syntax is available on:

- The Catalog > All assets page
- The Lineage page
- The asset health page
- The Insights page
- The alert policy creation page (when creating an asset alert)

## Next steps

- See the [asset selection syntax reference](/guides/build/assets/asset-selection-syntax/reference) for a full list of the filters, layers, operands, and functions that you can use to construct your own queries.
- Check out [example asset selection queries](/guides/build/assets/asset-selection-syntax/examples).
