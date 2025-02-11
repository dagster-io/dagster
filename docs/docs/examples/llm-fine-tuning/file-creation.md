---
title: File creation
description: File Creation and File Validation
last_update:
  author: Dennis Hume
sidebar_position: 40
---

Using the data we prepared in the [previous step](feature-engineering), we will create two files: a training file and a validation file. A training file provides the model with labeled data to learn patterns, while a validation file evaluates the model's performance on unseen data to prevent overfitting. These will be used in our OpenAI fine-tuning job to create our model. The columnar data from our DuckDB assets needs to be fit into messages that resemble the conversation a user would have with a chatbot. Here we can inject the values of those fields into conversations:

<CodeExample path="docs_projects/project_llm_fine_tune/project_llm_fine_tune/assets.py" language="python" lineStart="136" lineEnd="154"/>

The fine-tuning process does not need all the data prepared from `enriched_graphic_novels`. We will simply take a sample of the DataFrame and write it to a `.jsonl` file. The assets to create the training and validation set are very similar (only the filename is different). They will take in the `enriched_graphic_novels` asset, generate the prompts, and write the outputs to a file stored locally:

<CodeExample path="docs_projects/project_llm_fine_tune/project_llm_fine_tune/assets.py" language="python" lineStart="156" lineEnd="172"/>

:::note

Since these files save the data locally, it may not work with every type of deployment.

:::

## Validation

The files are ready, but before we send the data to OpenAI to perform the training job, we should do some validation. It is always a good idea to put checkpoints in place as your workflows become more involved. Taking the time to ensure our data if formatted correctly can save debugging time before we get other APIs involved.

Luckily, OpenAI provides a cookbook specifically about [format validation](https://cookbook.openai.com/examples/chat_finetuning_data_prep#format-validation). This contains a series of checks we can perform to ensure our data meets the requirements for OpenAI training jobs.

Looking at this notebook. This would make a great asset check. Asset checks help ensure the assets in our DAG meet certain criteria that we define. Asset checks look very similar to assets, but are connected directly to the asset and do not appear as a separate node within the DAG.

Since we want an asset check for both the training and validation files, we will write a general function that contains the logic from the cookbook:

<CodeExample path="docs_projects/project_llm_fine_tune/project_llm_fine_tune/assets.py" language="python" lineStart="192" lineEnd="237"/>

This looks like any other Python function, except it returns an `AssetCheckResult`, which is what Dagster uses to store the output of the asset check. Now we can use that function to create asset checks directly tied to our file assets. Again, they look similar to assets, except they use the `asset_check` decorator:

<CodeExample path="docs_projects/project_llm_fine_tune/project_llm_fine_tune/assets.py" language="python" lineStart="239" lineEnd="249"/>

## Next steps

- Continue this example with [OpenAI job](open-ai-job)