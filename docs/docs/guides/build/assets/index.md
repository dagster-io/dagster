---
description: Dagster asset definitions enable a declarative approach to data management, in which code is the source of truth on what data assets should exist and how those assets are computed.
sidebar_position: 20
title: Assets
canonicalUrl: "/guides/build/assets"
slug: "/guides/build/assets"
---

An **asset** is an object in persistent storage, such as a table, file, or persisted machine learning model. An **asset definition** is a description, in code, of an asset that should exist and how to produce and update that asset.

Asset definitions enable a declarative approach to data management, in which code is the source of truth on what data assets should exist and how those assets are computed. To learn how to define assets in code, see "[Defining assets](/guides/build/assets/defining-assets)".

**Materializing** an asset is the act of running its function and saving the results to persistent storage. You can materialize assets from the Dagster UI or by invoking [Python APIs](/api/dagster).

:::info Dagster+ credit consumption

Asset materializations count toward your Dagster+ credit usage, while asset observations do not. We recommend using asset observations when reporting events from external systems in Dagster instead of asset materializations to avoid consuming credits.

## Assets vs ops

Behind the scenes, the Python function in an asset is an [op](/guides/build/ops). A crucial distinction between asset definitions and ops is that asset definitions know about their dependencies, while ops do not. Ops aren't connected to dependencies until they're placed inside a graph. You do not need to use ops directly to use Dagster.
