---
title: Representing external data sources with external assets
sidebar_position: 80
sidebar_label: 'External data sources'
---

One of Dagster's goals is to present a single unified lineage of all of the data assets in an organization, even if those assets are orchestrated by systems other than Dagster.

With **external assets**, you can model assets orchestrated by other systems natively within Dagster, ensuring you have a comprehensive catalog of your organization's data. You can also create new data assets downstream of these external assets.

Unlike native assets, Dagster can't materialize external assets directly or put them in a schedule. In these cases, an external system must inform Dagster when an external asset is updated.

For example, external assets could be:

- Files in a data lake that are populated by a bespoke internal tool
- A CSV file delivered daily by SFTP from a partner
- A table in a data warehouse populated by another orchestrator

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Familiarity with [Assets](/guides/data-assets)
- Familiarity with [Sensors](/guides/sensors)
</details>

## Defining external assets

Let's say you have a partner who sends you raw transaction data by SFTP on an almost daily basis. This data is later cleaned and stored in an internal data lake.

Because the raw transaction data isn't materialized by Dagster, it makes sense to model it as an external asset. The following example accomplishes this by using `AssetSpec`:

<CodeExample filePath="guides/data-modeling/external-assets/creating-external-assets.py" language="python" />

Refer to the [`AssetSpec` API docs](/todo) for the parameters you can provide to an external asset.

## Recording materializations and metadata

When an external asset is modeled in Dagster, you also need to inform Dagster whenever the external asset is updated. You should also include any relevant metadata about the asset, such as the time it was last updated.

There are two main ways to do this:

- Pulling external assets events with sensors
- Pushing external asset events using Dagster's REST API

### Pulling with sensors

You can use a Dagster [sensor](/guides/sensors) to regularly poll the external system and pull information about the external asset into Dagster.

For example, here's how you would poll an external system like an SFTP server to update an external asset whenever the file is changed.

<CodeExample filePath="guides/data-modeling/external-assets/pulling-with-sensors.py" language="python" />

Refer to the [Sensors guide](/guides/sensors) for more information about sensors.

### Pushing with the REST API

You can inform Dagster that an external asset has materialized by pushing the event from an external system to the REST API. The following examples demonstrate how to inform Dagster that a materialization of the `raw_transactions` external asset has occurred.

The required headers for the REST API depend on whether you're using Dagster+ or OSS. Use the tabs to view an example API request for each Dagster type.

<Tabs>
<TabItem value="dagster-plus" label="Dagster+">

Authentication headers are required if using Dagster+. The request should made to your Dagster+ organization and a specific deployment in the organization.

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

</TabItem>
<TabItem value="oss" label="OSS">

Authentication headers aren't required if using Dagster OSS. The request should be pointed at your open source URL, which is `http://localhost:3000` in this example.

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

</TabItem>
</Tabs>

Refer to the [External assets REST API documentation](/todo) for more information.

## Modeling a graph of external assets

Like regular Dagster assets, external assets can have dependencies. This is useful when you want to model an entire data pipeline orchestrated by another system.

<CodeExample filePath="guides/data-modeling/external-assets/dag-of-external-assets.py" language="python" />
