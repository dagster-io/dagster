---
title: "Lesson 7: Practice: Create a weekly_update_schedule"
module: "dagster_essentials"
lesson: "7"
---

# Practice: Create a weekly_update_schedule

To practice what you’ve learned, add a schedule to `schedules/__init__.py` that:

- Is named `weekly_update_schedule`
- Materializes the `trips_by_week` asset
- Runs every Monday at midnight

---

## Check your work

The schedule you built should look similar to the code contained in the **View answer** toggle. Click to open it.

```python
from dagster import ScheduleDefinition

from ..jobs import weekly_update_job

weekly_update_schedule = ScheduleDefinition(
  job=weekly_update_job,
  cron_schedule="0 0 * * 1", # every Monday at midnight
)
```

**If there are differences**, compare what you wrote to the schedule above and change them, as this schedule will be used as-is in future lessons.