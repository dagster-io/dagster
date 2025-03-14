---
title: 'Asset selection'
sidebar_position: 1000
---

Dagster's asset selection syntax allows you to query and view assets within your data lineage graph. You can select upstream and downstream layers of the graph, use filters to narrow down your selection, and use functions to return the root or sink assets of a given selection.

With asset selection, you can:

- Select a set of assets to view in the Dagster UI
- Define a job in Python that targets a selection of assets
- List or materialize a set of assets using the [Dagster CLI](/api/python-api/cli#dagster-asset)

## Availability

In the **Dagster OSS UI**, the asset selection syntax is available on:

- The Asset Catalog
- The Global asset lineage page

In the **Dagster+ UI**, the asset selection syntax is available on:

- The Asset Catalog > All Assets page
- The Global asset lineage page
- The Asset Health page
- The Insights page
- The Alert Policy creation page (when creating an asset alert)

## Next steps

- See the [asset selection syntax reference](/guides/build/assets/asset-selection-syntax/reference) for a full list of the filters, layers, operands, and functions that you can use to construct your own queries.
- Check out [example asset selection queries](/guides/build/assets/asset-selection-syntax/examples).
