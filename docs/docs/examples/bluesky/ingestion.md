---
title: Ingestion
description: Ingesting data from Bluesky
last_update:
  author: Dennis Hume
sidebar_position: 20
---

This example showcases a full end-to-end analytics pipeline with Dagster. It starts by ingesting data, transforming the data and presenting it in a BI tool. This is a common order of operations in the data space and having each phase exist in the same framework helps to build more reliable applications. We will start with ingestion.

The data that serves the foundation for our project is [Bluesky](https://bsky.app/). Bluesky is a decentralized social media platform that allows users to post content. For the ingestion layer we want to extract data from Bluesky and load it into a [Cloudflare R2 Bucket](https://developers.cloudflare.com/r2/buckets/) which is a cloud-based object storage service compatible with S3. R2 will serve as our storage layer and where we model the data. But first we need to determine the best way to get data from Bluesky.

Because there is not an out of the box integration for Bluesky in Dagster, we will build our a custom <PyObject section="resources" module="dagster" object="ConfigurableResource"/>. Bluesky uses [atproto](https://docs.bsky.app/docs/advanced-guides/atproto) and provides an [SDK](https://docs.bsky.app/docs/get-started) which will serve as the backbone for our resource.

<CodeExample
  path="docs_projects/project_atproto_dashboard/project_atproto_dashboard/ingestion/resources.py"
  language="python"
  startAfter="start_resource"
  endBefore="end_resource"
/>

The most important part of our resource is that it returns the atproto client which our Dagster assets will use. The `_login` method will initialize the client and cache it within the resource. We do this because Bluesky has rate limits and initializing the client counts against that limit. We intend to run these assets separately, so we want to be as efficient with our API calls as possible.

With the client defined, we can move to the strategy for pulling from Bluesky. There is a lot of data we can potentially pull but we will focus around posts related to data. In Bluesky there is the idea of [starter packs](https://bsky.social/about/blog/06-26-2024-starter-packs) which are curated lists of users associated with specific domains. We will ingest the [Data People](https://blueskystarterpack.com/starter-packs/lc5jzrr425fyah724df3z5ik/3l7cddlz5ja24) pack. Using the atproto client we can get all the members of that starter pack.

<CodeExample
  path="docs_projects/project_atproto_dashboard/project_atproto_dashboard/ingestion/utils/atproto.py"
  language="python"
  startAfter="start_starter_pack"
  endBefore="end_starter_pack"
/>

The `get_all_feed_items` function is similar in using the atproto client to get information about individual feeds. This retrieves a lot more data and is where we will be most concerned about rate limiting (which we will cover in the [next section](/examples/bluesky/rate-limiting)). But now that we have everything we need to interact with Bluesky, we can create our assets.

## Extracting data

Our first asset (`starter_pack_snapshot`) is responsible for extracting the members of the Data People starter pack and loading the data into R2. Let's look at the asset decorator and parameters before getting into the logic of the function.

<CodeExample
  path="docs_projects/project_atproto_dashboard/project_atproto_dashboard/ingestion/definitions.py"
  language="python"
  startAfter="start_starter_pack_dec"
  endBefore="end_starter_pack_dec"
/>

First we can see that we are setting a static partition for the specific starter pack. Next an `automation_condition` is added. This is a simple way to set a schedule for this asset and ensure it runs every midnight. Finally we add `kinds` of `Python` and `group_name` of `ingestion` which will help us organize our assets in the Dagster UI. For the parameters we will use the `ATProtoResource` we created for Bluesky data and the Dagster maintained `S3Resource` which works for R2. Now we can walk through the logic of the function.

<CodeExample
  path="docs_projects/project_atproto_dashboard/project_atproto_dashboard/ingestion/definitions.py"
  language="python"
  startAfter="start_starter_pack_func"
  endBefore="end_starter_pack_func"
/>

Using the `ATProtoResource` we initialize the client and extract the members from the starter pack. That information is stored in R2 at a path defined by the current date. We also update a dynamic partition that is defined outside of this asset. This partition will be used by our next asset.

<CodeExample
  path="docs_projects/project_atproto_dashboard/project_atproto_dashboard/ingestion/definitions.py"
  language="python"
  startAfter="start_dynamic_partition"
  endBefore="end_dynamic_partition"
/>

Finally we set metadata about the file we saved in the Dagster asset catalog.

## Dynamic partitions

The next asset is `actor_feed_snapshot` where the feed data will be ingested. This asset will use the same resources as the `starter_pack_snapshot` asset and has a similar flow. The primary difference is that while `actor_feed_snapshot` had a single static partition, `actor_feed_snapshot` uses a dynamic partition.

<CodeExample
  path="docs_projects/project_atproto_dashboard/project_atproto_dashboard/ingestion/definitions.py"
  language="python"
  startAfter="start_actor_feed_snapshot"
  endBefore="end_actor_feed_snapshot"
/>

This asset will maintain a separate partition and execution for every member of the data starter pack and store a file in R2 at an object path specific to that user.

One other difference you may have noticed is the `automation_condition`. Because this is downstream of an asset on a schedule, we can set the condition to `dg.AutomationCondition.eager()` and it will execute immediately after its upstream dependency.

## Definition

This is everything we need for ingestion. At the bottom of the file we will set the <PyObject section="definitions" module="dagster" object="Definitions" />. This will contain all the assets and initialized resources.

<CodeExample
  path="docs_projects/project_atproto_dashboard/project_atproto_dashboard/ingestion/definitions.py"
  language="python"
  startAfter="start_def"
  endBefore="end_def"
/>

This definition is just one part of our overall project but it can be helpful to define separate definitions for more complicated projects devoted to specific domains. You will see the same pattern for the modeling and dashboard layers. All of these definitions will be merged into a final definition at the very end.

## Next steps

- Continue this example with [rate limiting](/examples/bluesky/rate-limiting)
