---
title: "Setting up custom logging"
sidebar_position: 20
---

# Custom loggers

Custom loggers are used to alter the structure of the logs being produced by your Dagster pipelines. For example, JSON logs can be produced to more easily be processed by log management systems.

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- A basic understanding of Dagster concepts such as assets, jobs and definitions
- A working knowledge of the Python logging module

</details>


## Step 1: Add a prebuilt custom logger to your jobs

This step shows how to add an existing custom logger, the `json_console_logger`, to your jobs. This will
override the default `colored_console_logger` and produce logs in JSON format.


### Add the custom logger to your asset jobs

The following example shows how to add the custom logger to your code location definitions and configure an asset job to use it.

<CodeExample filePath="guides/monitor-alert/custom-logging/asset-job-example.py" language="python" title="Add custom logger to asset job" />


### Add the custom logger to your ops-based jobs

Configuring a ops job to use the custom logger slightly differs from the asset job example. The following example shows how:

<CodeExample filePath="guides/monitor-alert/custom-logging/ops-job-example.py" language="python" title="Add custom logger to ops job" />


### Expected `json_console_logger` output

The `json_console_logger` will emit an exhaustive single line JSON document containing the full log record, including the dagster metadata fields.

Here's an example of the output for reference, formatted for readability:

```json
{
  "args": [],
  "created": 1725455358.2311811,
  "dagster_meta": {
    "dagster_event": null,
    "dagster_event_batch_metadata": null,
    "job_name": "hackernews_topstory_ids_job",
    "job_tags": {
      ".dagster/grpc_info": "{\"host\": \"localhost\", \"socket\": \"/var/folders/5b/t062dlpj3j716l4w1d3yq6vm0000gn/T/tmpds_hvzm9\"}",
      "dagster/preset_name": "default",
      "dagster/solid_selection": "*"
    },
    "log_message_id": "3850cfb8-f9fb-458a-a986-3efd26e4b859",
    "log_timestamp": "2024-09-04T13:09:18.225289",
    "op_name": "get_hackernews_topstory_ids",
    "orig_message": "Compute Logger - Got 500 top stories.",
    "resource_fn_name": null,
    "resource_name": null,
    "run_id": "11528a21-38d5-43e7-8b13-993e47ce7f7d",
    "step_key": "get_hackernews_topstory_ids"
  },
  "exc_info": null,
  "exc_text": null,
  "filename": "log_manager.py",
  "funcName": "emit",
  "levelname": "INFO",
  "levelno": 20,
  "lineno": 272,
  "module": "log_manager",
  "msecs": 231.0,
  "msg": "hackernews_topstory_ids_job - 11528a21-38d5-43e7-8b13-993e47ce7f7d - get_hackernews_topstory_ids - Compute Logger - Got 500 top stories.",
  "name": "dagster",
  "pathname": "/home/dagster/workspace/quickstart-etl/.venv/lib/python3.11/site-packages/dagster/_core/log_manager.py",
  "process": 35373,
  "processName": "SpawnProcess-2:1",
  "relativeCreated": 813.4410381317139,
  "stack_info": null,
  "thread": 8584465408,
  "threadName": "MainThread"
}
```

### Changing the logger configuration in the Dagster UI

You can also change the logger configuration in the Dagster UI. This is useful if you want to change the logger configuration without changing the code, to use the custom logger on a manual asset materialization launch, or change the verbosity of the logs.

```yaml
loggers:
  console:
    config:
      log_level: DEBUG
```

## Step 2: Write your custom logger

In this example, we'll create a logger implementation that produces comma separated values from selected fields in the
log record. Other examples can be found in the codebase, in the built-in loggers such as `json_console_logger`.

<CodeExample filePath="guides/monitor-alert/custom-logging/customlogger.py" language="python" title="Example custom logger" />

Sample output:

```csv
2024-09-04T09:29:33.643818,dagster,INFO,cc76a116-4c8f-400f-9c4d-c42b66cdee3a,topstory_ids_job,hackernews_topstory_ids,Compute Logger - Got 500 top stories.
```

The available fields emitted by the logger are defined in the [`LogRecord`](https://docs.python.org/3/library/logging.html#logrecord-objects) object.
In addition, Dagster specific information can be found in the `dagster_meta` attribute of the log record. The previous
example already some of these attributes.

It contains the following fields:

- `dagster_event`: string
- `dagster_event_batch_metadata`: string
- `job_name`: string
- `job_tags`: a dictionary of strings
- `log_message_id`: string
- `log_timestamp`: string
- `op_name`: string
- `run_id`: string
- `step_key`: string

## Next steps

Import your own custom logger by modifying the example provided in step 1.

## Limitations

It's not currently possible to globally configure the logger for all jobs in a repository.
