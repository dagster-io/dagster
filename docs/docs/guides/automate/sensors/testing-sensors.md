---
title: Testing sensors
sidebar_position: 300
---

<Tabs>
<TabItem value="Via the Dagster UI">

**Via the Dagster UI**

:::note

**Before you test:** Test evaluations of sensors run the sensor's underlying Python function, meaning that any side effects contained within that sensor's function may be executed.

:::

In the UI, you can manually trigger a test evaluation of a sensor and view the results.

1. Click **Overview > Sensors**.

2. Click the sensor you want to test.

3. Click the **Preview tick result** button, located near the top right corner of the page.

   ![Test sensor button](/images/guides/automate/sensors/test-sensor-button.png)

4. You'll be prompted to provide a cursor value (optional). You can use the existing cursor for the sensor (which will be prepopulated) or enter a different value. If you're not using cursors, leave this field blank.

   ![Cursor value field](/images/guides/automate/sensors/provide-cursor-page.png)

5. Click **Continue** to fire the sensor. A window containing the result of the evaluation will display, whether it's run requests, a skip reason, or a Python error:

   ![Evaluation result page](/images/guides/automate/sensors/eval-result-page.png)

6. If the preview was successful, then for each produced run request, you can view the run config and tags produced by that run request by clicking the **{}** button in the Actions column.

   ![Actions page in the Dagster UI](/images/guides/automate/sensors/actions-page.png)

7. Click the **Launch all & commit tick result** on the bottom right to launch all the run requests. It will launch the runs and link to the /runs page filtered to the IDs of the runs that launched.

   ![Runs page after launching all runs in the Dagster UI](/images/guides/automate/sensors/launch-all-page.png)

</TabItem>
<TabItem value="Via the CLI">

**Via the CLI**

To quickly preview what an existing sensor will generate when evaluated, run the following::

```shell
dagster sensor preview my_sensor_name
```

</TabItem>
<TabItem value="Via Python">

**Via Python**

To unit test sensors, you can directly invoke the sensor's Python function. This will return all the run requests yielded by the sensor. The config obtained from the returned run requests can be validated using the <PyObject section="execution" module="dagster" object="validate_run_config" /> function:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/sensors/sensors.py"
  startAfter="start_sensor_testing"
  endBefore="end_sensor_testing"
/>

Notice that since the context argument wasn't used in the sensor, a context object doesn't have to be provided. However, if the context object **is** needed, it can be provided via <PyObject section="schedules-sensors" module="dagster" object="build_sensor_context" />. Consider again the `my_directory_sensor_cursor` example:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/sensors/sensors.py"
  startAfter="start_cursor_sensors_marker"
  endBefore="end_cursor_sensors_marker"
/>

This sensor uses the `context` argument. To invoke it, we need to provide one:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/partitions_schedules_sensors/sensors/sensors.py"
  startAfter="start_sensor_testing_with_context"
  endBefore="end_sensor_testing_with_context"
/>

**Testing sensors with resources**

For sensors which utilize [resources](/guides/build/external-resources/), you can provide the necessary resources when invoking the sensor function.

Below is a test for the `process_new_users_sensor` that we defined in "[Using resources in sensors](/guides/automate/sensors/using-resources-in-sensors)", which uses the `users_api` resource.

<CodeExample
  path="docs_snippets/docs_snippets/concepts/resources/pythonic_resources.py"
  startAfter="start_test_resource_on_sensor"
  endBefore="end_test_resource_on_sensor"
  dedent="4"
/>

</TabItem>
</Tabs>
