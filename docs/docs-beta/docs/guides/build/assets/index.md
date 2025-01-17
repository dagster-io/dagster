---
title: Assets
sidebar_position: 10
---

An **asset** is an object in persistent storage, such as a table, file, or persisted machine learning model. An **asset definition** is a description, in code, of an asset that should exist and how to produce and update that asset.

Asset definitions enable a declarative approach to data management, in which code is the source of truth on what data assets should exist and how those assets are computed. To learn how to define assets in code, see "[Defining assets](defining-assets)".

**Materializing** an asset is the act of running its function and saving the results to persistent storage. You can materialize assets from the Dagster UI or by invoking [Python APIs](/api/python-api/).

:::note Assets vs ops

Behind the scenes, the Python function in an asset is an [op](/todo). A crucial distinction between asset definitions and ops is that asset definitions know about their dependencies, while ops do not. Ops aren't connected to dependencies until they're placed inside a graph. You do not need to use ops to use Dagster.

:::
