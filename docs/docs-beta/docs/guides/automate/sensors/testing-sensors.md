---
title: Testing sensors
sidebar_position: 300
---

<TabGroup>
<TabItem name="Via the Dagster UI">

### Via the Dagster UI

<Note>
  <strong>Before you test</strong>: Test evaluations of sensors run the sensor's
  underlying Python function, meaning that any side effects contained within
  that sensor's function may be executed.
</Note>

In the UI, you can manually trigger a test evaluation of a sensor and view the results.

1. Click **Overview > Sensors**.

2. Click the sensor you want to test.

3. Click the **Test Sensor** button, located near the top right corner of the page.

   <Image
   src="/images/concepts/partitions-schedules-sensors/sensors/test-sensor-button.png"
   width={592}
   height={270}
   />

4. You'll be prompted to provide a cursor value. You can use the existing cursor for the sensor (which will be prepopulated) or enter a different value. If you're not using cursors, leave this field blank.

   <Image
   src="/images/concepts/partitions-schedules-sensors/sensors/provide-cursor-page.png"
   width={900}
   height={454}
   />

5. Click **Evaluate** to fire the sensor. A window containing the result of the evaluation will display, whether it's run requests, a skip reason, or a Python error:

   <Image
   src="/images/concepts/partitions-schedules-sensors/sensors/eval-result-page.png"
   width={898}
   height={455}
   />

   If the run was successful, then for each produced run request, you can open the launchpad pre-scaffolded with the config produced by that run request. You'll also see a new computed cursor value from the evaluation, with the option to persist the value.

</TabItem>
<TabItem name="Via the CLI">

### Via the CLI

To quickly preview what an existing sensor will generate when evaluated, run the following::

```shell
dagster sensor preview my_sensor_name
```

</TabItem>
<TabItem name="Via Python">

### Via Python

To unit test sensors, you can directly invoke the sensor's Python function. This will return all the run requests yielded by the sensor. The config obtained from the returned run requests can be validated using the <PyObject object="validate_run_config" /> function:

```python file=concepts/partitions_schedules_sensors/sensors/sensors.py startafter=start_sensor_testing endbefore=end_sensor_testing
from dagster import validate_run_config


@sensor(target=log_file_job)
def sensor_to_test():
    yield RunRequest(
        run_key="foo",
        run_config={"ops": {"process_file": {"config": {"filename": "foo"}}}},
    )


def test_sensor():
    for run_request in sensor_to_test():
        assert validate_run_config(log_file_job, run_request.run_config)
```

Notice that since the context argument wasn't used in the sensor, a context object doesn't have to be provided. However, if the context object **is** needed, it can be provided via <PyObject object="build_sensor_context" />. Consider again the `my_directory_sensor_cursor` example:

```python file=concepts/partitions_schedules_sensors/sensors/sensors.py startafter=start_cursor_sensors_marker endbefore=end_cursor_sensors_marker
@sensor(target=log_file_job)
def my_directory_sensor_cursor(context):
    last_mtime = float(context.cursor) if context.cursor else 0

    max_mtime = last_mtime
    for filename in os.listdir(MY_DIRECTORY):
        filepath = os.path.join(MY_DIRECTORY, filename)
        if os.path.isfile(filepath):
            fstats = os.stat(filepath)
            file_mtime = fstats.st_mtime
            if file_mtime <= last_mtime:
                continue

            # the run key should include mtime if we want to kick off new runs based on file modifications
            run_key = f"{filename}:{file_mtime}"
            run_config = {"ops": {"process_file": {"config": {"filename": filename}}}}
            yield RunRequest(run_key=run_key, run_config=run_config)
            max_mtime = max(max_mtime, file_mtime)

    context.update_cursor(str(max_mtime))
```

This sensor uses the `context` argument. To invoke it, we need to provide one:

```python file=concepts/partitions_schedules_sensors/sensors/sensors.py startafter=start_sensor_testing_with_context endbefore=end_sensor_testing_with_context
from dagster import build_sensor_context


def test_my_directory_sensor_cursor():
    context = build_sensor_context(cursor="0")
    for run_request in my_directory_sensor_cursor(context):
        assert validate_run_config(log_file_job, run_request.run_config)
```

#### Testing sensors with resources

For sensors which utilize [resources](/concepts/resources), you can provide the necessary resources when invoking the sensor function.

Below is a test for the `process_new_users_sensor` that we defined in the [Using resources in sensors](#using-resources-in-sensors) section, which uses the `users_api` resource.

```python file=/concepts/resources/pythonic_resources.py startafter=start_test_resource_on_sensor endbefore=end_test_resource_on_sensor dedent=4
from dagster import build_sensor_context, validate_run_config

def test_process_new_users_sensor():
    class FakeUsersAPI:
        def fetch_users(self) -> list[str]:
            return ["1", "2", "3"]

    context = build_sensor_context()
    run_requests = process_new_users_sensor(context, users_api=FakeUsersAPI())
    assert len(run_requests) == 3
```

</TabItem>
</TabGroup>