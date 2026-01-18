# Replicate metadata from OSS to Dagster+

This example demonstrates how to replicate metadata from an existing Dagster open source instance in a new Dagster+ project.

## Existing metadata in OSS

First, imagine that you have a Dagster OSS project that has metadata set up. For example, you might have existing jobs written in `existing_definitions.py`.

Let's say that you have an asset called "my_daily_partitioned_asset" that look like this:

```python
@asset(partitions_def=DailyPartitionsDefinition(start_date="2023-10-01"))
def my_daily_partitioned_asset() -> MaterializeResult:
    some_metadata_value = random.randint(0, 100)

    return MaterializeResult(metadata={"foo": some_metadata_value})
```

Then, you may have several months of metadata for this asset that you want to replicate in Dagster+. In your OSS instance, it might look like this:

<img width="1464" alt="existing metadata in oss" src="https://github.com/dagster-io/dagster/assets/4531914/603fe9a2-4744-4a97-9ebf-3c64c128a99b">

## Replicate metadata in Dagster+

Now, as you've moved to Dagster+, you may want to replicate this metadata in Dagster+ to keep track of it. You can do this by creating a new job in the same OSS project. This job will read the metadata from the existing OSS storage and report it as new [external assets](https://docs.dagster.io/guides/build/assets/external-assets) to Dagster+.

### Step 1: Read the metadata from the existing OSS storage

You can get this information via DagsterInstance's [fetch_materializations](https://docs.dagster.io/api/python-api/internals#dagster.DagsterInstance.fetch_materializations) method:

```python
result: EventRecordsResult = context.instance.fetch_materializations(
    records_filter=AssetKey.from_user_string(asset_key),
    limit=1,
    cursor=cursor,
)
```

In this example, we are fetching the metadata for the asset with the key `asset_key` one by one. You can also fetch multiple at once by updating the `limit` parameter.

### Step 2: Create a job to send the metadata as new external assets to Dagster+

There are many ways to update external asset metadata. See the [documentation](https://docs.dagster.io/guides/build/assets/external-assets#recording-materializations-and-metadata) for more information.

In this example, we are using the [REST API](https://docs.dagster.io/api/python-api/external-assets-rest-api) to update the metadata and wrap it in a Dagster asset to maximize the observability of the process.

Note: This requires an agent token. Here are the instruction to get the agent token: https://docs.dagster.io/dagster-plus/deployment/management/tokens/agent-tokens

```python
url = "https://{organization}.dagster.cloud/{deployment_name}/report_asset_materialization/".format(
    organization="new_organization", deployment_name="new_deployment"
)

payload = {
    "asset_key": asset_key,
    "metadata": metadata,
    "partition": partition,
}
headers = {
    "Content-Type": "application/json",
    "Dagster-Cloud-Api-Token": new_dagster_cloud_api_token,
}

response = requests.request("POST", url, json=payload, headers=headers)
response.raise_for_status()
```

In this example, we are sending a POST request to the Dagster+ API with the asset key, metadata, and partition. You can also send multiple metadata at once by updating the payload.

### Step 3: Run the job

In this example, we are running the script in [a Dagster job](./metadata_to_plus/migrate_metadata_job.py) to replicate the recent 100 records. You can also run it in a one-off Python script or any other way that suits your needs. The benefit of running it in a Dagster job is that you can parameterize the job and monitor the progress and logs in the Dagster UI.

- Configure information such as the asset key, new org info in the Dagster UI:
  <img width="1464" alt="config" src="https://github.com/dagster-io/dagster/assets/4531914/7398cc90-f83b-4571-8a53-9830a7f109e5">
- Monitor progress and logs in the Dagster UI:
  <img width="1464" alt="logs in migrate job" src="https://github.com/dagster-io/dagster/assets/4531914/26b92b48-17a0-4c13-ab1a-42f3acb6a15b">

### Result in Dagster+

Left is the existing metadata in OSS, and right is the replicated metadata in Dagster+:

<img width="2560" alt="Screenshot 2024-06-10 at 2 14 04 PM" src="https://github.com/dagster-io/dagster/assets/4531914/8823c362-f301-468b-9db4-e072136a1a8f">
