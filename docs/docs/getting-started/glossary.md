---
description: 'Technical glossary defining key concepts: assets, definitions, partitions,
  resources, schedules, sensors, I/O managers, ops, jobs, and graphs.'
sidebar_position: 30
title: Glossary
unlisted: true
---

# Glossary

Dagster terminology used throughout the documentation is defined below. Each term links to the
corresponding section in the [concepts](concepts.md) page.

| Term | Definition |
| ---- | ---------- |
| [asset](concepts#asset) | An asset represents a logical unit of data such as a table, dataset, or machine learning model. Assets can depend on other assets, forming data lineage. |
| [asset check](concepts#asset-check) | Associated with an asset to ensure data quality, freshness, or completeness. Checks run when the asset executes and record the result. |
| [code location](concepts#code-location) | A collection of definitions deployed in a particular environment that specifies the Python environment and dependencies. Projects can have multiple code locations. |
| [component](concepts#component) | An opinionated project layout built around a `Definitions` object used to bootstrap reusable patterns. |
| [config](concepts#config) | A schema (``RunConfig``) that parameterizes a Dagster object at execution time, enabling reuse with different settings. |
| [definitions](concepts#definitions) | A top-level construct containing all Dagster objects in a project—assets, jobs, schedules, and more—that are deployed and visible in the UI. |
| [graph](concepts#graph) | Connects multiple ops to form a DAG. When working with assets directly, graphs are often unnecessary. |
| [io manager](concepts#io-manager) | Defines how data is stored and retrieved between executions of assets and ops. |
| [job](concepts#job) | The main unit of execution, consisting of a selection of assets or a graph of ops. |
| [op](concepts#op) | A computational unit of work arranged in a graph to control execution order; largely replaced by assets. |
| [partition](concepts#partition) | Represents a logical slice of a dataset or computation, enabling incremental processing of subsets. |
| [resource](concepts#resource) | A configurable external dependency such as a database or API. |
| [type](concepts#type) | Used to define and validate the data passed between ops. |
| [schedule](concepts#schedule) | Automates jobs or assets on a specified interval and can include run configuration. |
| [sensor](concepts#sensor) | Triggers jobs or assets in response to an external event and may include run configuration. |
