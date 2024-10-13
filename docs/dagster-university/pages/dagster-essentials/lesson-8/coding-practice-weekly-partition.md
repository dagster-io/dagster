---
title: 'Lesson 8: Practice: Create a weekly partition'
module: 'dagster_essentials'
lesson: '8'
---

# Practice: Create a weekly partition

To practice what you’ve learned, create a `weekly_partition` using Dagster’s `WeeklyPartitionsDefinition` with the same start and end dates.

---

## Check your work

The partition you built should look similar to the following code. Click **View answer** to view it.

**If there are differences**, compare what you wrote to the partition below and change them, as this partition will be used as-is in future lessons.

```python {% obfuscated="true" %}
from dagster import WeeklyPartitionsDefinition
from ..assets import constants

start_date = constants.START_DATE
end_date = constants.END_DATE

weekly_partition = WeeklyPartitionsDefinition(
    start_date=start_date,
    end_date=end_date
)
```
