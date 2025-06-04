---
title: Factory pipelines
description: Using factory pipelines
last_update:
  author: Dennis Hume
sidebar_position: 40
---

Dagster encourages software engineering best practices, one of which is keeping code [DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself). We saw the components for our podcast workflow and noted that everything exists within a factory function. Now we will show how to apply this factory to different podcasts and create distinct asset lineages for each, all within the same Dagster project.

If you look at the `rss_pipeline_factory` function, it returns a <PyObject section="definitions" module="dagster" object="Definitions" /> object containing the four assets, a job for those assets, and the sensor for the specific podcast feed:

<CodeExample
  path="docs_projects/project_dagster_modal_pipes/project_dagster_modal_pipes/defs/pipeline_factory.py"
  language="python"
  startAfter="start_def"
  endBefore="end_def"
/>

We will invoke that factory function for three podcasts:

<CodeExample
  path="docs_projects/project_dagster_modal_pipes/project_dagster_modal_pipes/definitions.py"
  language="python"
  startAfter="start_factory"
  endBefore="end_factory"
/>

Now we have a list of <PyObject section="definitions" module="dagster" object="Definitions" /> for the three podcasts. We will merge these together into a single definition in our Dagster project:

<CodeExample
  path="docs_projects/project_dagster_modal_pipes/project_dagster_modal_pipes/definitions.py"
  language="python"
  startAfter="start_def"
  endBefore="end_def"
/>

We can now see all the assets in Dagster and know that we will ingest any new podcasts going forward.

![2048 resolution](/images/examples/modal/screenshot_dagster_lineage.png)
