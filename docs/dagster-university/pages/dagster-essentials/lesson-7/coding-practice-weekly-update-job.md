---
title: 'Lesson 7: Practice: Create a weekly_update_job'
module: 'dagster_essentials'
lesson: '7'
---

# Practice: Create a weekly_update_job

To practice what you’ve learned, add a job to `jobs/__init__.py` that will materialize the `trips_by_week` asset.

---

## Check your work

The job you built should look similar to the following code. Click **View answer** to view it.

**If there are differences**, compare what you wrote to the job below and change them, as this job will be used as-is in future lessons.

```python {% obfuscated="true" %}
from dagster import define_asset_job, AssetSelection

trips_by_week = AssetSelection.assets(["trips_by_week"])

weekly_update_job = define_asset_job(
    name="weekly_update_job",
    selection=trips_by_week,
)
```
