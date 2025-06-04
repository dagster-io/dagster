---
title: RSS Assets
description: Processing RSS feeds
last_update:
  author: Dennis Hume
sidebar_position: 30
---

The Modal application is ready, so we can return to Dagster and define the upstream and downstream assets that will tie our pipeline together. First, we need to download the RSS feed and upload it to the R2 bucket:

<CodeExample
  path="docs_projects/project_dagster_modal_pipes/project_dagster_modal_pipes/defs/pipeline_factory.py"
  language="python"
  startAfter="start_podcast_audio"
  endBefore="end_podcast_audio"
/>

Now that the data is in R2, as Modal expects, we can invoke the Modal application via Dagster. We will do this using [Dagster Pipes](/guides/build/external-pipelines/). Pipes provide a wrapper around a subprocess. This is ideal for executing code in other environments, and also allows us to pass Dagster any necessary context or environment variables to Modal. This is particularly helpful for things like the access keys for the R2 Bucket. Using the Dagster `ModalClient` from the [`dagster-modal`](/integrations/libraries/modal) integration, we can invoke the Modal application:

<CodeExample
  path="docs_projects/project_dagster_modal_pipes/project_dagster_modal_pipes/defs/pipeline_factory.py"
  language="python"
  startAfter="start_transcription"
  endBefore="end_transcription"
/>

Using pipes, Modal will emit events back to Dagster so Dagster can monitor and wait for the Modal application to finish running. Dagster will then continue the orchestration of our assets and move on to the next step after the transcribed text files are uploaded to R2.

The next asset will take those new files and summarize them with OpenAI. After a summary has been created, we can use <PyObject section="assets" module="dagster" object="MaterializeResult" /> to record the summary text and the associated R2 key within the Dagster Catalog:

<CodeExample
  path="docs_projects/project_dagster_modal_pipes/project_dagster_modal_pipes/defs/pipeline_factory.py"
  language="python"
  startAfter="start_summary"
  endBefore="end_summary"
/>

The final step in our DAG pipeline emails the summary to the user with [yagmail](https://github.com/kootenpv/yagmail).

## Sensor

We have defined all the assets needed to transcribe and summarize a podcast. Now we want to make sure we are notified of new podcasts as soon as they are available. We can define a [sensor ](/guides/automate/sensors/) in Dagster to check the podcast URL and determine if any new podcasts have been uploaded. To do this, we want to check the `etag` of the RSS feed. The sensor will be responsible for maintaining a cursor of tags and determining if there have been any podcasts not yet processed. This way, the first time we start our Dagster sensor, it will execute a run for each podcast, but after that initial execution, the sensor will only look for new podcasts that are uploaded:

<CodeExample
  path="docs_projects/project_dagster_modal_pipes/project_dagster_modal_pipes/defs/pipeline_factory.py"
  language="python"
  startAfter="start_sensor"
  endBefore="end_sensor"
/>

## Factory method

That is all we need for our podcast workflow. We now want to apply this to multiple podcasts. Luckily, the code has already accounted for that. You may have noticed that the assets and sensors we have created are parameterized. This is because all of this work exists within a factory function:

<CodeExample
  path="docs_projects/project_dagster_modal_pipes/project_dagster_modal_pipes/defs/pipeline_factory.py"
  language="python"
  startAfter="start_factory"
  endBefore="end_factory"
/>

We use this factory to reuse the components and apply them to multiple RSS feeds. In the next section, we will discuss some of the best practices around the factory pattern in Dagster.

## Next steps

- Continue this example with [factory pipeline](/examples/modal/factory-pipeline)
