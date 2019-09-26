# dagster-papertrail

##Introduction
This library provides an integration with [Papertrail](https://papertrailapp.com) for logging.

## Example
You can easily set up your Dagster pipeline to log to Papertrail. You'll need an active Papertrail
account, and have your papertrail URL and port handy. Starting with a simple hello world pipeline,
you can configure it to use Papertrail logging as follows:

```python
from dagster import pipeline, solid, ModeDefinition
from dagster_papertrail import papertrail_logger

@solid
def hello_logs(context):
    context.log.info('Hello, world!')

@pipeline(
    mode_defs=[ModeDefinition(logger_defs={'papertrail': papertrail_logger})]
)
def hello_pipeline():
    hello_logs()

```

Just provide your environment configuration:

```yaml
loggers:
  papertrail:
    config:
      log_level: 'INFO'
      name: 'hello_pipeline'
      papertrail_address: YOUR_PAPERTRAIL_URL
      papertrail_port: YOUR_PAPERTRAIL_PORT
```

and you're off to the races!
