---
title: Open AI Job
description: Execute the Open AI Fine-Tuning Job
last_update:
  author: Dennis Hume
sidebar_position: 50
---

Now that we are confident in the files we have generated, we can kickoff our OpenAI fine-tuning job. The first step is uploading the files to the OpenAI storage endpoint. Like DuckDB, Dagster offers a resource to interact with OpenAI and provide us with a client we can use. After the files have been uploaded, OpenAI will return a file id which we will need for the fine-tuning job.

We have an asset for each file to upload but like the file creation, they will look very similar:

```python
@dg.asset(
    kinds={"openai"},
    description="Upload training set",
    group_name="fine_tuning",
)
def upload_training_file(
    context: dg.AssetExecutionContext,
    openai: OpenAIResource,
    training_file,
) -> str:
    with openai.get_client(context) as client:
        with open(training_file, "rb") as file_fd:
            response = client.files.create(file=file_fd, purpose="fine-tune")
    return response.id
```

## Fine-Tuning Job

We can now fine-tune our model. Using the OpenAI resource again we will use the fine-tuning endpoint and submit a job using our two files. Executing a fine-tuning job may take a while so after we submit it, we will want to the asset to poll and wait for it to succeed:

```python
@dg.asset(
    kinds={"openai"},
    description="Exeute model fine-tuning job",
    group_name="fine_tuning",
)
def fine_tuned_model(
    context: dg.AssetExecutionContext,
    openai: OpenAIResource,
    upload_training_file,
    upload_validation_file,
) -> str:
    with openai.get_client(context) as client:
        create_job_resp = client.fine_tuning.jobs.create(
            training_file=upload_training_file,
            validation_file=upload_validation_file,
            model=constants.MODEL_NAME,
            suffix="goodreads",
        )

    create_job_id = create_job_resp.to_dict()["id"]
    context.log.info(f"Fine tuning job: {create_job_id}")

    while True:
        status_job_resp = client.fine_tuning.jobs.retrieve(create_job_id)
        status = status_job_resp.to_dict()["status"]
        context.log.info(f"Job {create_job_id}: {status}")
        if status in ["succeeded", "cancelled", "failed"]:
            break
        time.sleep(30)

    fine_tuned_model_name = status_job_resp.to_dict()["fine_tuned_model"]
    context.add_output_metadata({"model_name": fine_tuned_model_name})
    return fine_tuned_model_name
```

After the fine-tuning job has succeeded, we are given the unique name of our new model (in this case `ft:gpt-4o-mini-2024-07-18:test:goodreads:AoAYW0x3`). We can record this as metadata so it can be used over time.

Now that we have a model, we should test if it is an improvement over our initial model.

## Next steps

- Continue this tutorial with [model validation](model_validation)