---
title: Modal Application
description: Using Modal with Dagster
last_update:
  author: Dennis Hume
sidebar_position: 20
---

For this example, we will create multiple pipelines that do the following:

- Download audio files
- Transcribe the audio
- Summarize the audio
- Send an email summary

Many of these steps can be done in Dagster, but the transcription step is better suited for a different environment.

An advantage of Dagster is that you are not limited to only executing code with Dagster. In this case, we will use [Modal](https://modal.com/). Modal makes it easy to manage and scale the infrastructure needed to perform distributed computation while maintaining a Pythonic workflow. It works especially well with Dagster, since Dagster can help manage and orchestrate the various components in our pipeline, while Modal can be used to spin up auto-scaling infrastructure in a serverless way.

We will start by explaining the Modal application of our pipeline and then show how we can use it within Dagster.

## Modal application

Within Modal, we need to define the image that will be used by the Modal infrastructure. As mentioned, Modal allows you to define an image and the desired dependencies in a Pythonic way so you can avoid defining a separate `Dockerfile`. The app image is then supplied to the `modal.App, which we will use later on to decorate our Modal functions:

<CodeExample
  path="docs_projects/project_dagster_modal_pipes/modal_project/transcribe.py"
  language="python"
  startAfter="start_app"
  endBefore="end_app"
/>

Another benefit of Modal is that it allows us to mount a [Cloudflare R2 Bucket](https://developers.cloudflare.com/r2/buckets/) like a file system. R2 will serve as the staging ground between Dagster and Modal:

<CodeExample
  path="docs_projects/project_dagster_modal_pipes/modal_project/transcribe.py"
  language="python"
  startAfter="start_mount"
  endBefore="end_mount"
/>

With the image and R2 mount ready, we can define our Modal functions. The first function will transcribe a segment of a podcast. Because Modal scales to fit the needs of the application and allows for parallel processing, we can optimize our application by splitting podcasts that may be several hours into smaller pieces. Modal will manage all of the infrastructure provisioning as needed. As you can see in the decorator, all we need to provide Modal with is our image, the R2 bucket, and our required CPUs (we could use GPUs but the OpenAI Whisper model is relatively small and does not require GPU processing like some other models):

<CodeExample
  path="docs_projects/project_dagster_modal_pipes/modal_project/transcribe.py"
  language="python"
  startAfter="start_transcribe_segment"
  endBefore="end_transcribe_segment"
/>

The next function, `transcribe_episode`, will split an audio file into smaller segments and then apply the `transcribe_segment` function. After all the segments have been processed, it will write the transcribed text into JSON files within the R2 bucket:

<CodeExample
  path="docs_projects/project_dagster_modal_pipes/modal_project/transcribe.py"
  language="python"
  startAfter="start_segment"
  endBefore="end_segment"
/>

With the Modal functions in place, we can define the entry point `main`. This is what Dagster will use to interact with Modal:

<CodeExample
  path="docs_projects/project_dagster_modal_pipes/modal_project/transcribe.py"
  language="python"
  startAfter="start_main"
  endBefore="end_main"
/>

## Next steps

- Continue this example with [rss assets](/examples/modal/rss-assets)
