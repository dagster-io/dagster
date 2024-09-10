---
title: Representing external data sources with external assets
sidebar_position: 80
sidebar_label: 'External data assets'
---

One of Dagster's goals is to present a single unified lineage of all of the data assets in an organization. This can include assets orchestrated by Dagster and assets orchestrated by other systems.

**External assets** enable you to model assets orchestrated by other systems natively within Dagster's Asset catalog, and create new data assets downstream of these external assets.

External assets differ from native Dagster assets in that Dagster can't materialize them directly or put them on a schedule. Instead, an external system must inform Dagster of when an external asset is updated.

Examples of external assets could be files in a data lake that are populated by a bespoke internal tool, a CSV file delivered daily by SFTP from a partner, or a table in a data warehouse populated by another orchestrator.

## What you'll learn

- How to create external assets
- How to create assets that depend on external assets
- How to record materializations and metadata
- How to model a DAG of multiple external assets

---

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- A basic understanding of Dagster and assets. See the [Quick Start](/getting-started/quickstart) tutorial for an overview.
- Familiarity with [Sensors](/guides/sensors)
</details>

---

## Creating and depending on external assets

Let's imagine that we have a partner that sends us some raw transaction data by SFTP on, roughly, a daily basis, that's later cleaned and stored in an internal data lake. Because the raw transaction data isn't materialized by Dagster, it makes sense to model it as an external asset.

<CodeExample filePath="guides/data-modeling/external-assets/creating-external-assets.py" language="python" title="Creating an external asset" />

See the [AssetSpec API docs](/todo) for all the potential parameters you can provide to an external asset.

## Recording materializations and metadata

In the preceding example, we modeled the external asset in the asset graph. We also need to inform Dagster whenever an external asset is updated, and include any relevant metadata about the asset.

There are two main ways to do this: "pulling" external assets events with sensors, and "pushing" external asset events using the REST API.

### "Pulling" with sensors

You can use a Dagster [sensor](/guides/sensors) to regularly poll the external system and "pull" information about the external asset into Dagster.

For example, here's how you would poll an external system (like an SFTP server) to update an external asset whenever the file is changed.

<CodeExample filePath="guides/data-modeling/external-assets/pulling-with-sensors.py" language="python" title="Pulling external asset events with sensors" />

See the [sensors guide](/guides/sensors) for more information about sensors.

### "Pushing" with the REST API

You can inform Dagster that an external asset has materialized by "pushing" the event from an external system to the REST API.

For example, here's how we would inform Dagster of a materialization of the `raw_transactions` external asset in Dagster+:

```shell
curl \
  -X POST \
  -H 'Content-Type: application/json' \
  -H 'Dagster-Cloud-Api-Token: [YOUR API TOKEN]' \
  'https://[YOUR ORG NAME].dagster.cloud/[YOUR DEPLOYMENT NAME]/report_asset_materialization/' \
  -d '
{
  "asset_key": "raw_transactions",
  "metadata": {
    "file_last_modified_at_ms": 1724614700266
  }
}'
```

If you're using open source, you don't need the authentication headers and should point it at your open source URL (in this example, `http://localhost:3000`):

```shell
curl \
  -X POST \
  -H 'Content-Type: application/json' \
  'http://localhost:3000/report_asset_materialization/' \
  -d '
{
  "asset_key": "raw_transactions",
  "metadata": {
    "file_last_modified_at_ms": 1724614700266
  }
}'
```

See the [external assets REST API docs](/todo) for more information.

## Modeling a DAG of external assets

Like regular Dagster assets, external assets can have dependencies. This is useful when you want to model an entire data pipeline orchestrated by another system.

<CodeExample filePath="guides/data-modeling/external-assets/dag-of-external-assets.py" language="python" title="External assets with dependencies" />
