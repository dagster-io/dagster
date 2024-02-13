---
title: 'Lesson 7: Updating the Definitions object'
module: 'dagster_essentials'
lesson: '7'
---

# Updating the Definitions object

Before the jobs and schedules can be used, you’ll need to add them to the `Definitions` object.

---

## Adding jobs to Definitions

Revisiting the definitions in the top level `__init__.py` file, the first step to adding the schedule to the code location is adding the jobs for the schedules to use.

The `jobs` argument of the `Definitions` object accepts a list of jobs. To add jobs to the code location:

1. Add the following to the imports, which will bring in the jobs you created:

   ```python
   from .jobs import trip_update_job, weekly_update_job
   ```

   This tells Dagster to import the `trip_update_job` and `weekly_update_job` schedules from `.jobs`, or `jobs/__init__.py`.

2. Beneath `metric_assets = load_assets_from_modules([metrics])`, add the following:

   ```python
   all_jobs = [trip_update_job, weekly_update_job]
   ```

   This creates a variable named `all_jobs` that contains a list of jobs. Right now, that’s only `trip_update_jobs` and `weekly_update_jobs`, but other jobs can be added in the future.

3. In the `Definitions` object, add the `jobs` parameter and set it to equal `all_jobs`:

   ```python
   jobs=all_jobs,
   ```

At this point, `__init__.py` should look like this:

```python
from dagster import Definitions, load_assets_from_modules

from .assets import trips, metrics
from .resources import database_resource
from .jobs import trip_update_job, weekly_update_job

trip_assets = load_assets_from_modules([trips])
metric_assets = load_assets_from_modules([metrics])

all_jobs = [trip_update_job, weekly_update_job]

defs = Definitions(
    assets=[*trip_assets, *metric_assets],
    resources={
        "database": database_resource,
    },
    jobs=all_jobs,
)
```

---

## Adding schedules to Definitions

Now that you’ve added the jobs, let’s add the schedules to the `Definitions` object:

1. In the imports section at the top of the file, add the following:

   ```python
   from .schedules import trip_update_schedule, weekly_update_schedule
   ```

   This tells Dagster to import the `trip_update_schedule` and `weekly_update_schedule` schedules from `.schedules`, or `schedules/__init__.py`.

2. Beneath `metric_assets = load_assets_from_modules([metrics])`, add the following:

   ```python
   all_schedules = [trip_update_schedule, weekly_update_schedule]
   ```

   This creates a variable named `all_schedules` that contains a list of schedules. Right now, that’s only `trip_update_schedule` and `weekly_update_schedule`, but other schedules can be added in the future.

3. In the `Definitions` object, add the `schedules` parameter and set the value to `all_schedules`:

   ```python
   schedules=all_schedules,
   ```

At this point, `__init__.py` should look like this:

```python
from dagster import Definitions, load_assets_from_modules

from .assets import trips, metrics
from .resources import database_resource
from .jobs import trip_update_job, weekly_update_job
from .schedules import trip_update_schedule, weekly_update_schedule

trip_assets = load_assets_from_modules([trips])
metric_assets = load_assets_from_modules([metrics])

all_jobs = [trip_update_job, weekly_update_job]
all_schedules = [trip_update_schedule, weekly_update_schedule]


defs = Definitions(
    assets=[*trip_assets, *metric_assets],
    resources={
        "database": database_resource,
    },
    jobs=all_jobs,
    schedules=all_schedules,
)
```
