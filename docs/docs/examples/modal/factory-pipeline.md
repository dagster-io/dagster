---
title: Factory pipelines
description: Using factory pipelines
last_update:
  author: Dennis Hume
sidebar_position: 40
---

Dagster encourages software engineering best practices, one of which is keeping code [DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself). We will apply our factory pipeline to multiple podcasts which will create distinct asset lineages for each podcast, all within the same Dagster project.

If you look at the `rss_pipeline_factory` function, it returns a <PyObject section="definitions" module="dagster" object="Definitions" /> object containing the four assets, a job for those assets, and the sensor for the specific podcast feed. All of those pipelines use the same <PyObject section="resources" module="dagster" object="ConfigurableResource"/> which we can set at the project level:

<CodeExample
  path="docs_projects/project_dagster_modal_pipes/src/project_dagster_modal_pipes/defs/resources.py"
  language="python"
  startAfter="start_resources"
  endBefore="end_resources"
  title="src/project_dagster_modal_pipes/defs/resources.py"
/>

With the resources set, the last step will be to initialize our three podcasts:

<CodeExample
  path="docs_projects/project_dagster_modal_pipes/src/project_dagster_modal_pipes/defs/feeds.py"
  language="python"
  startAfter="start_def"
  endBefore="end_def"
  title="src/project_dagster_modal_pipes/defs/feeds.py"
/>

We can now see all the assets in Dagster and know that we will ingest any new podcasts going forward.

![2048 resolution](/images/examples/modal/screenshot_dagster_lineage.png)
