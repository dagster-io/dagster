---
title: 'Lesson 9: Creating a job'
module: 'dagster_essentials'
lesson: '9'
---

# Creating a job

Next, you’ll create a job that materializes the new `adhoc_request` asset. This job will be nearly identical to the jobs from Lesson 7.

Navigate to the `jobs/__init__.py` file and add the following lines to create a job for your ad-hoc requests

```python
adhoc_request = AssetSelection.assets(["adhoc_request"])

adhoc_request_job = define_asset_job(
    name="adhoc_request_job",
    selection=adhoc_request,
)
```

You’ll also have to update an existing job, `trip_update_job`. The initial `AssetSelection.all()` this job uses will select the new `adhoc_request` asset, but we don’t want that. Just like how you omitted the `trips_by_week` asset in the asset selection, let’s also omit the `adhoc_request` asset, as shown below:

```python
trip_update_job = define_asset_job(
    name="trip_update_job",
    partitions_def=monthly_partition,
    selection=AssetSelection.all() - trips_by_week - adhoc_request
)
```
