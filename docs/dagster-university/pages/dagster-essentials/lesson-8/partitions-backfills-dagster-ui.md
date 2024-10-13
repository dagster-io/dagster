---
title: 'Lesson 8: Partitions and backfills in the Dagster UI'
module: 'dagster_essentials'
lesson: '8'
---

# Partitions and backfills in the Dagster UI

Now that you've created your partitions, used those partitions in the assets, and updated the jobs with partitions to create a partitioned schedule, let’s check out how things look in the Dagster UI. If you still have `dagster dev` running, you’ll need to **Reload definitions** to ensure the partitions are visible.

---

## Viewing and materializing assets with partitions

{% table %}

- Step one

---

- {% width="60%" %}
  Navigate to **Assets**, then **Asset lineage**. As you’ll see in the asset graph, the `taxi_trips` assets now have partition information.

- ![Assets with partitions in the Dagster UI](/images/dagster-essentials/lesson-8/ui-assets-with-partitions.png) {% rowspan=2 %}

{% /table %}

{% table %}

- Step two

---

- {% width="60%" %}
  Taking a closer look at the `taxi_trips_file` asset, there are three partitions that represent the three months that were included in the partition.

  - ⚫ **0** - represents that 0 partitions have been successfully materialization
  - **O All** represents all (three) partitions haven't yet been materialized
  - **⚠️ 0** represents that there are zero failed partitions

  This information is useful to get a quick look at the state of your asset.

- ![The taxi_trips_file asset with new partitions](/images/dagster-essentials/lesson-8/ui-taxi-trips-file-asset.png) {% rowspan=2 %}

{% /table %}

{% table %}

- Step three

---

- {% width="60%" %}
  Clicking **Materialize all** will display a popup containing the partition information.

  This allows you to choose which partitions you want to materialize or launch a backfill that can materialize several partitions at once.

- ![A popup displaying an asset's partition information in the Dagster UI](/images/dagster-essentials/lesson-8/ui-asset-partition-info.png) {% rowspan=2 %}

{% /table %}

---

## Launching a backfill

{% table %}

- Step one

---

- {% width="60%" %}
  To begin the backfill, click **Launch backfill** in the popup window from the last section. By default, the date range will be the entire date range.

  Next, click **Overview > Backfills** to view the backfill’s information.

- ![The Backfills tab in the Dagster UI](/images/dagster-essentials/lesson-8/ui-backfills-tab.png) {% rowspan=2 %}

{% /table %}

{% table %}

- Step two

---

- {% width="60%" %}
  Click on a backfill to open its details page. In this page, you’ll see each asset being materialized in the backfill, along with their status.

- ![The Backfill details page in the Dagster UI](/images/dagster-essentials/lesson-8/ui-backfill-details-page.png) {% rowspan=2 %}

{% /table %}

{% table %}

- Step three

---

- {% width="60%" %}
  Navigate back to the **Global Asset Lineage** page (**Assets > Asset lineage).**

  In the asset graph, you’ll see the status of the partitioned and non-partitioned assets has been updated.

- ![The Global Asset Lineage page with updated asset information after a backfill](/images/dagster-essentials/lesson-8/ui-updated-asset-graph.png) {% rowspan=2 %}

{% /table %}

---

## Viewing asset partition details

{% table %}

- Step one

---

- {% width="60%" %}
  In the asset graph, click the `taxi_trips` asset and view in the **Asset Catalog**. Each month is listed as a partition that can be examined.

- ![The Asset partition details page in the Dagster UI](/images/dagster-essentials/lesson-8/ui-asset-partition-details.png) {% rowspan=2 %}

{% /table %}

{% table %}

- Step two

---

- {% width="60%" %}
  Select **2023-03-01** to view a specific partition. Here you can see information specific to that partition of the asset, including lineage to the source data. In this case, that’s `taxi_trips_file`.

- ![Details for the 2023-03-01 partition in the Dagster UI](/images/dagster-essentials/lesson-8/ui-partition-details.png) {% rowspan=2 %}

{% /table %}
