---
title: 'Programmatically defining dependencies using asset factories'
sidebar_position: 60
sidebar_label: 'Asset Factories (2)'
---

In data engineering, it's often helpful to reuse code to define similar assets. For example, you may want to represent every file in a directory as an asset.

Additionally, you may be serving stakeholders who aren't familiar with Python or Dagster. They may prefer interacting with assets using a domain-specific language (DSL) built on top of a configuration language such as YAML.

Using an asset factory reduces complexity and creates a pluggable entry point to define additional assets.

<details>
  <summary>Prerequisites</summary>

This guide builds upon the concepts in the [asset factories](/guides/asset-factories) tutorial.
</details>

---

## Building an asset factory in Python

Imagine a data analytics team that maintains a large number of tables. To support analytics needs, the team runs queries and constructs new tables from the results.

Each table can be represented in YAML by a name, upstream asset dependencies, and a query:
<CodeExample filePath="guides/data-modeling/asset-factories-with-deps/table_definitions.yaml" language="yaml" title="YAML Definition for ETL tables" />

Here's how you might add Python logic to define these assets in Dagster.

<CodeExample filePath="guides/data-modeling/asset-factories-with-deps/asset-factory-with-deps.py" language="python" title="Programmatically defining asset dependencies" />

## Defining dependencies between factory assets and regular assets

Here's how you might add Python logic to define a Dagster asset downstream of factory assets:

<CodeExample filePath="guides/data-modeling/asset-factories-with-deps/asset_downstream_of_factory_assets.py" language="python" title="Defining dependencies between factory assets and regular assets" />
