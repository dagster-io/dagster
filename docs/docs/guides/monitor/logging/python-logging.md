---
title: 'Python logging'
sidebar_position: 200
---

Dagster is compatible and configurable with [Python's logging module](https://docs.python.org/3/library/logging.html). Configuration options are set in a [`dagster.yaml` file](/guides/deploy/dagster-yaml), which will apply the contained settings to any run launched from the instance.

Configuration settings include:

- The Python loggers to capture from
- The log level loggers are set to
- The handlers/formatters used to process log messages produced by runs

## Relevant APIs

| Name                                                                         | Description                                                                             |
| ---------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| <PyObject section="utilities" module="dagster" object="get_dagster_logger"/> | A function that returns a Python logger that will automatically be captured by Dagster. |

## Production environments and event log storage

In a production context, it's recommended that you be selective about which logs are captured. It's possible to overload the event log storage with these events, which may cause some pages in the UI to take a long time to load.

To mitigate this, you can:

- Capture only the most critical logs
- Avoid including debug information if a large amount of run history will be maintained

## Capturing Python logs \{#capturing-python-logs}

By default, logs generated using the Python logging module aren't captured into the Dagster ecosystem. This means that they aren't stored in the Dagster event log, will not be associated with any Dagster metadata (such as step key, run ID, etc.), and won't show up in the default view of the [Dagster UI](/guides/operate/webserver).

For example, imagine you have the following code:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/logging/python_logger.py"
  startAfter="start_python_logger"
  endBefore="end_python_logger"
/>

Because this code uses a custom Python logger instead of `context.log`, the log statement won't be added as an event to the Dagster event log or show up in the UI.

However, this default behavior can be changed to treat these sort of log statements the same as `context.log` calls. This can be accomplished by setting the `managed_python_loggers` key in `dagster.yaml` file to a list of Python logger names that you would like to capture:

<CodeExample
  language="yaml"
  path="docs_snippets/docs_snippets/concepts/logging/python_logging_managed_loggers_config.yaml"
/>

Once this key is set, Dagster will treat any normal Python log call from one of the listed loggers in the exact same way as a `context.log` call. This means you should be able to see this log statement in the UI:

![Log Python error](/images/guides/monitor/logging/log-python-error.png)

:::note

If `python_log_level` is set, the loggers listed here will be set to the given level before a run is launched. Refer to the [Configuring global log levels](#configuring-global-log-levels) for more info and an example.

:::

## Configuring global log levels \{#configuring-global-log-levels}

To set a global log level in a Dagster instance, set the `python_log_level` parameter in your instance's `dagster.yaml` file.

This setting controls the log level of all loggers managed by Dagster. By default, this will just be the `context.log` logger. If there are custom Python loggers that you want to capture, refer to the [Capturing Python logs section](#capturing-python-logs).

Setting a global log level allows you to filter out logs below a given level. For example, setting a log level of `INFO` will filter out all `DEBUG` level logs:

<CodeExample
  language="yaml"
  path="docs_snippets/docs_snippets/concepts/logging/python_logging_python_log_level_config.yaml"
/>

## Configuring Python log handlers

In your `dagster.yaml` file, you can configure handlers, formatters and filters that will apply to the Dagster instance. This will apply the same logging configuration to all runs.

For example:

<CodeExample language="yaml" path="docs_snippets/docs_snippets/concepts/logging/python_logging_handler_config.yaml" />

Handler, filter and formatter configuration follows the [dictionary config schema format](https://docs.python.org/3/library/logging.config.html#logging-config-dictschema) in the Python logging module. Only the `handlers`, `formatters` and `filters` dictionary keys will be accepted, as Dagster creates loggers internally.

From there, standard `context.log` calls will output with the configured handlers, formatters and filters. After execution, read the output log file `my_dagster_logs.log`. As expected, the log file contains the formatted log:

![Log file output](/images/guides/monitor/logging/log-file-output.png)

## Examples

### Creating a captured Python logger without modifying dagster.yaml

To create a logger that's captured by Dagster without modifying your `dagster.yaml` file, use the <PyObject section="utilities" module="dagster" object="get_dagster_logger"/> utility function. This pattern is useful when logging from inside nested functions, or other cases where it would be inconvenient to thread through the context parameter to enable calls to `context.log`.

For example:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/logging/python_logger.py"
  startAfter="start_get_logger"
  endBefore="end_get_logger"
/>

:::note

The logging module retains global state, meaning the logger returned by this function will be identical if <PyObject section="utilities" module="dagster" object="get_dagster_logger" /> is called multiple times with the same arguments in the same process. This means that there may be unpredictable or unituitive results if you set the level of the returned Python logger to different values in different parts of your code.

:::

### Outputting Dagster logs to a file

If you want to output all Dagster logs to a file, use the Python logging module's built-in [`logging.FileHandler`](https://docs.python.org/3/library/logging.handlers.html#logging.FileHandler) class. This sends log output to a disk file.

To enable this, define a new `myHandler` handler in your `dagster.yaml` file to be a `logging.FileHandler` object:

<CodeExample
  language="yaml"
  path="docs_snippets/docs_snippets/concepts/logging/python_logging_file_output_config.yaml"
/>

You can also configure a formatter to apply a custom format to the logs. For example, to include a timestamp with the logs, we defined a custom formatter named `timeFormatter` and attached it to `myHandler`.

If we execute the following job:

<CodeExample
  path="docs_snippets/docs_snippets/concepts/logging/file_output_pipeline.py"
  startAfter="start_custom_file_output_log"
  endBefore="end_custom_file_output_log"
/>

And then read the `my_dagster_logs.log` output log file, we'll see the log file contains the formatted log:

![Log file output](/images/guides/monitor/logging/log-file-output.png)
