---
title: 'Lesson 8: Creating a schedule with a date-based partition'
module: 'dagster_essentials'
lesson: '8'
---

# Creating a schedule with a date-based partition

In the previous lesson, you created the `trip_update_job` job that updates most of your assets. The job was put on a schedule that updates the assets on the fifth day of every month at midnight.

Now that you’ve partitioned the relevant assets, the schedule can be changed to only get the latest month’s data and not refresh the entirety of the asset. This is best practice and saves time on compute to limit intake of only new data.

Currently, `trip_update_job` in `jobs/__init__.py` should look like this:

```python
trip_update_job = define_asset_job(
    name="trip_update_job",
    selection=AssetSelection.all() - AssetSelection.assets(["trips_by_week"]),
)
```

To add partition to the job, make the following changes:

1. Import the `monthly_partition` from `partitions`:

   ```python
   from ..partitions import monthly_partition
   ```

2. In the job, add a `partitions_def` parameter equal to `monthly_partition`:

   ```python
   partitions_def=monthly_partition,
   ```

The job should now look like this:

```python
from dagster import define_asset_job, AssetSelection
from ..partitions import monthly_partition

trips_by_week = AssetSelection.assets("trips_by_week")

trip_update_job = define_asset_job(
    name="trip_update_job",
    partitions_def=monthly_partition, # partitions added here
    selection=AssetSelection.all() - trips_by_week
)
```
