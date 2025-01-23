---
title: Factory pipelines
description: Using factory pipelines
last_update:
  author: Dennis Hume
sidebar_position: 40
---

Dagster encourages software engineering best practices. One of which is keeping code DRY. We saw the components for our podcast workflow and noted that everything exists within a factory function. Now we will show how to apply this factory to different podcasts and create distinct asset lineages for each, all within the same Dagster project.

If you look at the `rss_pipeline_factory` function, it returns a `Definitions` objects containing the four assets, a job for those assets and the sensor for that the specific podcast feed:

<CodeExample path="project_dagster_modal_pipes/project_dagster_modal_pipes/pipeline_factory.py" language="python" lineStart="209" lineEnd="219"/>

We will invoke that factory function for three podcasts:

<CodeExample path="project_dagster_modal_pipes/project_dagster_modal_pipes/definitions.py" language="python" lineStart="22" lineEnd="41"/>

Now we have a list of `Definitions` for the three podcasts. We will merge these together into a single definition in our Dagster project:

<CodeExample path="project_dagster_modal_pipes/project_dagster_modal_pipes/definitions.py" language="python" lineStart="43" lineEnd="53"/>

We can now see all the assets in Dagster and know that we will ingest any new podcasts going foward.

![2048 resolution](/images/tutorial/modal/screenshot_dagster_lineage.png)
