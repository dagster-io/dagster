---
title: 'Lesson 7: Creating a schedule'
module: 'dagster_essentials'
lesson: '7'
---

# Creating a schedule

Now that you know what makes up a schedule, let’s create one. To do this, we’ll use the `ScheduleDefinition` class.

Copy and paste the following snippet into `schedules/__init__.py`:

```python
from dagster import ScheduleDefinition
from ..jobs import trip_update_job

trip_update_schedule = ScheduleDefinition(
    job=trip_update_job,
    cron_schedule="0 0 5 * *", # every 5th of the month at midnight
)
```

Let’s look at what this code does:

1. Imports the `ScheduleDefinition` class
2. From the `jobs` module, import the `trip_update_job` job
3. Used `ScheduleDefinition` to create a schedule that:
   - Is attached to the `trip_update_job` job
   - Has a cron expression of `0 0 5 * *`
