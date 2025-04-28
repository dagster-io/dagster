---
title: Rate limiting
description: Handling rate limiting in assets
last_update:
  author: Dennis Hume
sidebar_position: 30
---

One of the hurdles in getting data from Bluesky is working within the rate limits. Let's go back and look at the `get_all_feed_items` function that extracts feed information. This function uses [tenacity](https://tenacity.readthedocs.io/en/latest/) to handle retries for the function `_get_feed_with_retries` and will back off requests if we begin to hit our limits.

<CodeExample
  path="docs_projects/project_atproto_dashboard/project_atproto_dashboard/ingestion/utils/atproto.py"
  language="python"
  startAfter="start_all_feed_items"
  endBefore="end_all_feed_items"
/>

Then if we look at the `actor_feed_snapshot` asset that uses `get_all_feed_items`, you will see one additional parameter in the decorator.

<CodeExample
  path="docs_projects/project_atproto_dashboard/project_atproto_dashboard/ingestion/definitions.py"
  language="python"
  startAfter="start_concurrency"
  endBefore="end_concurrency"
/>

This tells the asset to use the concurrency defined in the `dagster.yaml` which is a top level configuration of the Dagster instance.

<CodeExample
  path="docs_projects/project_atproto_dashboard/dagster.yaml"
  language="yaml"
  startAfter="start_concurrency"
  endBefore="end_concurrency"
/>

We already mentioned that the `actor_feed_snapshot` asset is dynamically partitioned by user feeds. This means that without setting concurrency controls, all of those segments within the partition would execute in parallel. Given that Bluesky is the limiting factor, and the shared resource client by all of the assets, we want to ensure that only one asset is running at a time. Applying the concurrency control ensures that Dagster will do this without having to add additional code to our assets.

Now that we know how to extract data and store all this data, we can talk about how to model it.

## Next steps

- Continue this example with [modeling](/examples/bluesky/modeling)
