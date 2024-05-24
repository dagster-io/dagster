---
title: 'Lesson 9: Updating the Definitions object'
module: 'dagster_essentials'
lesson: '9'
---

# Updating the Definitions object

As with your other Dagster definitions, the final step is to add the sensor, its related asset, and job into the `Definitions` object. This will be done in the top-level `__init__.py` file.

1. Import the new asset, job, and sensor into the `__init__.py` file by updating the following imports:

   ```python
   from .assets import trips, metrics, requests
   ...
   from .jobs import trip_update_job, weekly_update_job, adhoc_request_job
   ...
   from .sensors import adhoc_request_sensor
   ```

2. Beneath `metric_assets`, create a `request_assets` variable that loads the assets from `requests`:

   ```python
   request_assets = load_assets_from_modules([requests])
   ```

3. Add the `adhoc_request_job` to `all_jobs` :

   ```python
   all_jobs = [trip_update_job, weekly_update_job, adhoc_request_job]
   ```

4. Beneath `all_schedules`, create a new variable named `all_sensors` and add the `adhoc_request_sensor` to it:

   ```python
   all_sensors = [adhoc_request_sensor]
   ```

5. Lastly, update the `Definitions` object by:

   1. Adding the new asset (`request_assets`) to the `assets` parameter:

      ```python
      assets=[*trip_assets, *metric_assets, *request_assets],
      ```

   2. Adding the `sensors` parameter and setting it to `all_sensors`:

      ```python
      sensors=all_sensors,
      ```

At this point, `__init__.py` should look like this:

```python
from dagster import Definitions, load_assets_from_modules

from .assets import trips, metrics, requests
from .resources import database_resource
from .jobs import trip_update_job, weekly_update_job, adhoc_request_job
from .schedules import trip_update_schedule, weekly_update_schedule
from .sensors import adhoc_request_sensor

trip_assets = load_assets_from_modules([trips])
metric_assets = load_assets_from_modules([metrics])
request_assets = load_assets_from_modules([requests])

all_jobs = [trip_update_job, weekly_update_job, adhoc_request_job]
all_schedules = [trip_update_schedule, weekly_update_schedule]
all_sensors = [adhoc_request_sensor]

defs = Definitions(
    assets=[*trip_assets, *metric_assets, *request_assets],
    resources={
        "database": database_resource,
    },
    jobs=all_jobs,
    schedules=all_schedules,
    sensors=all_sensors
)
```

Congratulations on creating a sensor! We’ll discuss how to enable the sensor in a bit, but let’s start by going through the Dagster UI.
