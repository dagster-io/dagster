# dagster-datadog

##Introduction
This library provides an integration with Datadog, to support publishing metrics to Datadog from within Dagster solids.

## Getting Started

This library uses the Python [datadogpy](https://github.com/DataDog/datadogpy) library. To use it, you'll first need to create a DataDog account and get both [API and Application keys](https://docs.datadoghq.com/account_management/api-app-keys/).

This integration uses [DogStatsD](https://docs.datadoghq.com/developers/dogstatsd/), so you'll need to ensure the datadog agent is running on the host you're sending metrics from.

## Posting to DataDog

You can easily publish metrics from Dagster with the `datadog` resource:

```python
@solid(required_resource_keys={'datadog'})
def datadog_solid(context):
    context.resources.datadog.event('Man down!', 'This server needs assistance.')
    context.resources.datadog.gauge('users.online', 1001, tags=["protocol:http"])
    context.resources.datadog.increment('page.views')
    context.resources.datadog.decrement('page.views')
    context.resources.datadog.histogram('album.photo.count', 26, tags=["gender:female"])
    context.resources.datadog.distribution('album.photo.count', 26, tags=["color:blue"])
    context.resources.datadog.set('visitors.uniques', 999, tags=["browser:ie"])
    context.resources.datadog.service_check('svc.check_name', context.resources.datadog.WARNING)
    context.resources.datadog.timing("query.response.time", 1234)

    # Use timed decorator
    @context.resources.datadog.timed('run_fn')
    def run_fn():
        pass

    run_fn()

@pipeline(mode_defs=[ModeDefinition(resource_defs={'datadog': datadog_resource})])
def dd_pipeline():
    datadog_solid()

result = execute_pipeline(
    dd_pipeline,
    {'resources': {'datadog': {'config': {'api_key': 'YOUR_KEY', 'app_key': 'YOUR_KEY'}}}},
)

```
