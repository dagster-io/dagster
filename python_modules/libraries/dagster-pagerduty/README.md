# dagster-pagerduty

##Introduction
This library provides an integration with PagerDuty, to support creating alerts from your Dagster
code.

Presently, it provides a thin wrapper on the [Events V2 API](https://v2.developer.pagerduty.com/docs/events-api-v2).

## Getting Started
You can install this library with:

```
pip install dagster_pagerduty
```

To use this integration, you'll first need to create a PagerDuty integration. There are [PagerDuty instructions here](https://support.pagerduty.com/docs/services-and-integrations#section-events-api-v2) for creating a new PagerDuty service & integration.

As noted in the PagerDuty documentation, you'll find an integration key (also referred to as a "routing key") on the Integrations tab for your new service. This key is used to authorize events created from the PagerDuty events API.

Once your service/integration is created, you can provision a PagerDuty resource and issue PagerDuty alerts from within your solids. A simple example is shown below:

```
@solid
def pagerduty_solid(context):
    context.resources.pagerduty.EventV2_create(
        summary='alert from dagster'
        source='localhost',
        severity='error',
        event_action='trigger',
    )

pipeline = PipelineDefinition(
    name='test_pagerduty_resource',
    solids=[pagerduty_solid],
    mode_definitions=[ModeDefinition(resources={'pagerduty': pagerduty_resource})],
)

execute_pipeline(
    pipeline,
    {
        'resources': {
            'pagerduty': {'config': {'routing_key': '0123456789abcdef0123456789abcdef'}}
        }
    },
)
```
