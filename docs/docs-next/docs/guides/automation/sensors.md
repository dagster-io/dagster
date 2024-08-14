### Basic Sensor Example 

This example includes a `check_for_new_files` function that simulates finding new files. In a real scenario, this function would check an actual system or directory.

The sensor runs every 5 seconds. If it finds new files, it starts a run of `my_job`. If not, it skips the run and logs "No new files found" in the Dagster UI.

<CodeExample filePath="guides/automation/simple-sensor-example.py" language="python" title="Simple Sensor Example" />

:::tip

By default, sensors aren't enabled when first deployed to a Dagster instance.
Click "Automation" in the top navigation to find and enable a sensor.

:::