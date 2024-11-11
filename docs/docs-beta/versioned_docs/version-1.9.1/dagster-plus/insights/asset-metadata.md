---
title: "Integrate asset metadata into Dagster+ Insights"
sidebar_label: "Integrate asset metadata"
sidebar_position: 1
---

Out of the box, Dagster+ Insights gives you visibility into a variety of common metrics across your data platform.
By creating custom metrics from asset metadata, you can use Insights to perform historical aggregation on any
data your assets can emit.

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need a Dagster+ account on the Pro plan.

</details>

## Step 1: Emit numeric metadata on your assets at runtime

You'll need one or more assets that emit the same metadata key at run time. Insights metrics
are most valuable when you have multiple assets that emit the same kind of metadata, such as
such as the number of rows processed or the size of a file uploaded to object storage.

Follow [the metadata guide](/guides/metadata#runtime-metadata) to add numeric metadata
to your asset materializations.

## Step 2: Enable viewing your metadata in Dagster+ Insights

Once your assets are emitting numeric metadata values, you'll be able to enable viewing them in the Insights UI.

To add your metadata key to the list of metrics shown in Insights, click **Edit** in the sidebar next to the **User provided metrics** header:

![Viewing the Insights tab in the Dagster+ UI](/img/placeholder.svg)
{/* <Image
alt="Viewing the Insights tab in the Dagster UI"
src="/images/dagster-cloud/insights/insights-tab.png"
width={2640}
height={1516}
*/}

In the dialog that appears, use the eye indicator to show or hide metrics in Insights. Selected metrics will be visible in both the Insights sidebar and on individual asset pages.

:::note

It may take up to 24 hours for Insights to ingest new metadata. If this is a newly added metadata key and
it isn't showing up in the list of metrics that can be displayed, try again in a few hours.

:::

## Step 3: Customize how your metric is displayed in Insights

You can also change a metric's icon, display name, and description by clicking the **pencil icon** next to the metric
in the **Edit** dialog.

If the metric you're tracking is directly associated with a cost, you can input the cost per unit in the **Estimate costs** tab. Insights will
use this to show an estimated cost alongside any aggregations of that metric.

![Cost editor dialog](/img/placeholder.svg)
