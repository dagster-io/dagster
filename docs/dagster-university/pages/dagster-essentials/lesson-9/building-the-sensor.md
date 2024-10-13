---
title: 'Lesson 9: Building the sensor'
module: 'dagster_essentials'
lesson: '9'
---

# Building the sensor

With the new asset and configuration set up, let’s create a sensor that reacts to events by materializing the `adhoc_request` asset.

As a high-level overview, we’ll listen for new requests as JSON files in the `data/requests` directory, assume that the file has valid values, and trigger a run of the `adhoc_request_job` with the configuration set as the values in the request. This run’s configuration will be available to the `adhoc_request` asset during its materialization.

---

## Sensor cursors

Before we dive into building, however, let’s take a moment to discuss sensor **cursors.**

A cursor is a stored value used to manage the state of the sensor. The sensor you’ll build uses its cursor to keep track of what requests it has already made a report for. Other use cases for a cursor are to store the ID of the last fetched record, or where the computation last left off.

Your sensor will retrieve all the file names in the `data/requests` directory, compare it to the list of files it already looked at and stored in its stateful cursor, update the cursor with the new files, and kick off a new run for each file.

Most sensors follow a similar lifecycle:

1. Read its cursor
2. Make a new observation and compare it to the cursor
3. If there have been any changes, make a run for each new change
4. Update the cursor to reflect the changes

---

## Writing the sensor

Now that cursors have been explained, let’s start writing the sensor.

1. Navigate to and open `sensors/__init__.py` in your Dagster project.

2. Add the following imports to the top of the file:

   ```python
   from dagster import (
       RunRequest,
       SensorResult,
       sensor
   )

   import os
   import json

   from ..jobs import adhoc_request_job
   ```

   Let’s break down these imports:

   - A `RunRequest` is used to trigger runs from a job, often with a specified configuration
   - `SensorResult` is the bundle of information returned after a sensor evaluates the condition
   - `sensor` is a decorator you’ll use to define that the function you’re writing is a sensor
   - The `os` standard library will be used to look at the files in the `data/requests` directory
   - The `json` standard library will be used to read the request’s JSON files as needed
   - `adhoc_request_job` is used to specify that the sensor will create runs from this job

3. To define a sensor, create a new function definition that takes `context` as a parameter. Similar to how your asset definitions had a context argument of type `AssetExecutionContext`, sensor definitions also have a similar `SensorEvaluationContext` to provide information and metadata about the currently running sensor. Your code should look like the snippet below:

   ```python
   from dagster import sensor, SensorEvaluationContext

   @sensor
   def adhoc_request_sensor(context: SensorEvaluationContext):
   ```

4. Annotate the function with the `@sensor` decorator and pass `adhoc_request_job` as an argument for the job parameter. At this point, your code should look like this:

   ```python
   @sensor(
       job=adhoc_request_job
   )
   def adhoc_request_sensor(context: SensorEvaluationContext):
   ```

5. Let’s fill out the function’s body. Create a variable that resolves to the `data/requests` directory, which is the directory the sensor will observe:

   ```python
   @sensor(
       job=adhoc_request_job
   )
   def adhoc_request_sensor(context: SensorEvaluationContext):
       PATH_TO_REQUESTS = os.path.join(os.path.dirname(__file__), "../../", "data/requests")
   ```

6. Next, define the cursor. Copy and paste the following code into the sensor’s function body:

   ```python
   previous_state = json.loads(context.cursor) if context.cursor else {}
   current_state = {}
   ```

   Let’s take a moment to break down what this does. The `context` argument stores the cursor used to manage the state of what the sensor has already looked at. The cursor may or may not exist, depending on if the sensor has previously had a tick run.

   To accommodate for this, we check if `context.cursor` exists and if it does, convert its string value into JSON. We also initialize the `current_state` to an empty object, which we’ll use to override the cursor after it reads through the directory.

7. Next, initialize an empty list called `runs_to_request`. This will be used to store the new requests we want to create runs for:

   ```python
   runs_to_request = []
   ```

8. Copy and paste the following into the sensor, and then we’ll discuss what it does:

   ```python
   for filename in os.listdir(PATH_TO_REQUESTS):
       file_path = os.path.join(PATH_TO_REQUESTS, filename)
       if filename.endswith(".json") and os.path.isfile(file_path):
           last_modified = os.path.getmtime(file_path)

           current_state[filename] = last_modified

           # if the file is new or has been modified since the last run, add it to the request queue
           if filename not in previous_state or previous_state[filename] != last_modified:
               with open(file_path, "r") as f:
                   request_config = json.load(f)

                   runs_to_request.append(RunRequest(
                       run_key=f"adhoc_request_{filename}_{last_modified}",
                       run_config={
                           "ops": {
                               "adhoc_request": {
                                   "config": {
                                       "filename": filename,
                                       **request_config
                                   }
                               }
                           }
                       }
                   ))
   ```

   **Note**: When pasting this into the sensor, verify that the indentation is correct or you'll encounter a Python error.

   This example:

   - Uses `os.listdir`  to iterate through the `data/requests` directory, looking at every JSON file, and seeing if it’s been updated or looked at it before in `previous_state`
   - Creates a `RunRequest` for the file if it's been updated or a report hasn’t been run before
   - Constructs a unique `run_key`, which includes the name of the file and when it was last modified
   - Passes the `run_key` into the `RunRequest`'s configuration using the `run_config` argument. By using the `adhoc_request` key, you specify that the `adhoc_request` asset should use the config provided.

9. Sensors expect a `SensorResult` returned, which contains all the information for the sensor, such as which runs to trigger and what the new cursor is. Append the following to the end of the sensor function:

   ```python
   return SensorResult(
       run_requests=runs_to_request,
       cursor=json.dumps(current_state)
   )
   ```

Putting everything together, you should have the following code in `sensors/__init__.py`:

```python
from dagster import (
    RunRequest,
    SensorEvaluationContext,
    SensorResult,
    sensor,
)

import os
import json

from ..jobs import adhoc_request_job

@sensor(
    job=adhoc_request_job
)
def adhoc_request_sensor(context: SensorEvaluationContext):
    PATH_TO_REQUESTS = os.path.join(os.path.dirname(__file__), "../../", "data/requests")

    previous_state = json.loads(context.cursor) if context.cursor else {}
    current_state = {}
    runs_to_request = []

    for filename in os.listdir(PATH_TO_REQUESTS):
        file_path = os.path.join(PATH_TO_REQUESTS, filename)
        if filename.endswith(".json") and os.path.isfile(file_path):
            last_modified = os.path.getmtime(file_path)

            current_state[filename] = last_modified

            # if the file is new or has been modified since the last run, add it to the request queue
            if filename not in previous_state or previous_state[filename] != last_modified:
                with open(file_path, "r") as f:
                    request_config = json.load(f)

                    runs_to_request.append(RunRequest(
                        run_key=f"adhoc_request_{filename}_{last_modified}",
                        run_config={
                            "ops": {
                                "adhoc_request": {
                                    "config": {
                                        "filename": filename,
                                        **request_config
                                    }
                                }
                            }
                        }
                    ))

    return SensorResult(
        run_requests=runs_to_request,
        cursor=json.dumps(current_state)
    )
```
