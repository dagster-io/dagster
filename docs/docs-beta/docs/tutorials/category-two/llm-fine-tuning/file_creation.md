---
title: File Creation
description: File Creation and File Validation
last_update:
  author: Dennis Hume
sidebar_position: 40
---

Using the data we just prepared, we need to create two files: a training and validation file. A training file provides the model with labeled data to learn patterns, while a validation file evaluates the model's performance on unseen data to prevent overfitting. These will be used in our OpenAI fine-tuning job to create our model. The columnar data from our DuckDB assets needs to be fit into messages that resemble the conversation a user would have with a chatbot. Here we can inject the values of those fields from into conversations:

```python
def create_prompt_record(data: dict, categories: list):
    return {
        "messages": [
            {
                "role": "system",
                "content": f"Given an author, title and book description, what category is it? Here are the possible categories {", ".join(categories)}",
            },
            {
                "role": "user",
                "content": f"What category is {data['title']} by {data["author"]}? Description: {data["description"]}",
            },
            {
                "role": "assistant",
                "content": data["category"],
                "weight": 1,
            },
        ]
    }
```

The fine-tuning process does not need all the data prepared from `enriched_graphic_novels`. We will simply take a sample of the DataFrame and write it to a `.jsonl` file. The assets to create the training and validation set are very similar (only the file name is different). They will take in the `enriched_graphic_novels` asset, generate the prompts, and write the outputs to a file stored locally:

```python
@dg.asset(
    group_name="preparation",
    description="Generate training file",
)
def training_file(
    config: ModelConfig,
    enriched_graphic_novels,
) -> str:
    graphic_novels = enriched_graphic_novels.sample(n=config.training_file_num)
    prompt_data = []
    for record in [row for _, row in graphic_novels.iterrows()]:
        prompt_data.append(create_prompt_record(record))

    file_name = "goodreads-training.jsonl"
    utils.write_openai_file(file_name, prompt_data)
    return file_name
```

:::note
Since these files save the data locally, it may not work with every type of deployment.
:::

## Validation

The files are ready but before we send the data to OpenAI to perform the training job, we should do some validation. It is always a good idea to put checkpoints in place as your workflows become more involved. Taking the time to ensure our data if formatted correctly can save debugging time before we get other APIs involved.

Luckily, OpenAI provides a cookbook specifically about [format validation](https://cookbook.openai.com/examples/chat_finetuning_data_prep#format-validation). This contains a serious checks we can perform to ensure our data meets the requirements for OpenAI training jobs.

Looking at this notebook. This would make a great asset check. Asset checks help ensure the assets in our DAG meet certain criteria that we define. Writing asset checks look very similar to assets but are connected directly to the asset and do not appear as a separate node within the DAG.

Since we want an asset check for both the training and validation files, we will write a general function that contains the logic from the cookbook:

```python
def openai_file_validation(file_name: str) -> Iterable:
    format_errors = defaultdict(int)
    for ex in utils.read_openai_file(file_name):
        if not isinstance(ex, dict):
            format_errors["data_type"] += 1
            continue

        messages = ex.get("messages", None)
        if not messages:
            format_errors["missing_messages_list"] += 1
            continue

        for message in messages:
            if "role" not in message or "content" not in message:
                format_errors["message_missing_key"] += 1

            if any(
                k not in ("role", "content", "name", "function_call", "weight")
                for k in message
            ):
                format_errors["message_unrecognized_key"] += 1

            if message.get("role", None) not in (
                "system",
                "user",
                "assistant",
                "function",
            ):
                format_errors["unrecognized_role"] += 1

            content = message.get("content", None)
            function_call = message.get("function_call", None)

            if (not content and not function_call) or not isinstance(content, str):
                format_errors["missing_content"] += 1

        if not any(message.get("role", None) == "assistant" for message in messages):
            format_errors["example_missing_assistant_message"] += 1

    if format_errors:
        yield dg.AssetCheckResult(
            passed=False,
            severity=dg.AssetCheckSeverity.ERROR,
            description="Training data set has errors",
            metadata=format_errors,
        )
    else:
        yield dg.AssetCheckResult(
            passed=True,
            description="Training data set is ready to upload",
        )
```

This looks like any other python function except it returns an `AssetCheckResult` which is what Dagster uses to store the output of the asset check. Now we can use that function to create asset checks directly tied to our file assets. Again they look similar to assets except for using the `asset_check` decorator:

```python
@dg.asset_check(
    asset=training_file,
    description="Validation for fine-tuning data file from OpenAI cookbook",
    metadata={
        "source": "https://cookbook.openai.com/examples/chat_finetuning_data_prep#format-validation"
    },
)
def training_file_format_check():
    openai_file_validation("goodreads-training.jsonl")
```

## Next steps

- Continue this tutorial with [open ai job](open_ai_job)