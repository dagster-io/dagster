---
title: 'Lesson 4: Overview'
module: 'dagster_essentials'
lesson: '4'
---

# Overview

In the previous lesson, you learned what an asset is and applied that knowledge to create your first assets in Dagster. Now, you’ll learn how to expand your Dagster project to create a data pipeline.

Data pipelines are a chain of events that produce data assets. As introduced in [Lesson 1](https://www.notion.so/Lesson-1-Introduction-43c6dcd35f6b4a6bb0729d3fd185ce88?pvs=21), Dagster empowers you to efficiently create data pipelines that produce multiple assets.

Now, you’ll build a complete data pipeline that:

- Loads your downloaded files into a database
- Combines and aggregates your data into metrics about taxi trips
- Visualizes those metrics and saves the report

While doing so, you’ll learn how to use Dagster to define dependencies between assets to produce pipelines.
