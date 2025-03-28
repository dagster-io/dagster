---
title: OpenAI Job
description: Execute the OpenAI Fine-Tuning Job
last_update:
  author: Dennis Hume
sidebar_position: 50
---

Now that we are confident in the files we have generated, we can kick off our OpenAI fine-tuning job. The first step is uploading the files to the OpenAI storage endpoint. Like DuckDB, Dagster offers a resource to interact with OpenAI and provide us with a client we can use. After the files have been uploaded, OpenAI will return a file ID, which we will need for the fine-tuning job.

We have an asset for each file to upload, but as in the file creation step, they will look similar:

<CodeExample
  path="docs_projects/project_llm_fine_tune/project_llm_fine_tune/assets.py"
  language="python"
  startAfter="start_upload_file"
  endBefore="end_upload_file"
/>

## Fine-tuning job

We can now fine-tune our model. Using the OpenAI resource again, we will use the fine-tuning endpoint and submit a job using our two files. Executing a fine-tuning job may take a while, so after we submit it, we will want to the asset to poll and wait for it to succeed:

<CodeExample
  path="docs_projects/project_llm_fine_tune/project_llm_fine_tune/assets.py"
  language="python"
  startAfter="start_fine_tuned_model"
  endBefore="end_fine_tuned_model"
/>

After the fine-tuning job has succeeded, we are given the unique name of our new model (in this case `ft:gpt-4o-mini-2024-07-18:test:goodreads:AoAYW0x3`). Note that we used `context.add_output_metadata` to record this as metadata as it will be good to track all the fine-tuned models we create over time with this job.

Now that we have a model, we should test if it is an improvement over our initial model.

## Next steps

- Continue this example with [model validation](/examples/llm-fine-tuning/model-validation)
