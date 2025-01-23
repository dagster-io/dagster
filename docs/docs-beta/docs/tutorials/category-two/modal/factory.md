---
title: Definitions
description: Using the factory within the Definitions
last_update:
  author: Dennis Hume
sidebar_position: 20
---

A key feature of Dagster is that it encourages software engineering best practices. One of which is keeping code DRY. We have everything we need to transcribe a podcast, but we want to apply it to several different podcasts and include all those assets within our Dagster project. You already saw how `rss_pipeline_factory` function returns a `Definitions` objects containing all the assets, jobs and sensors needed. We will invoke that factory function for each of the podcast feeds we are interested in:

<CodeExample path="project_dagster_modal_pipes/project_dagster_modal_pipes/definitions.py" language="python" lineStart="22" lineEnd="41"/>

Now we have a list of `Definitions`. We will merge these together into a single definition that we can use for our Dagster project. Since all the factory compnents use the same underlying resources we include those as well.

<CodeExample path="project_dagster_modal_pipes/project_dagster_modal_pipes/definitions.py" language="python" lineStart="43" lineEnd="53"/>

This gives us distinct assets and lineage for each of the podcasts we are interested in.