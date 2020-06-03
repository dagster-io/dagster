from datadog import DogStatsd, initialize, statsd

from dagster import Field, resource


class DataDogResource:
    '''This resource is a thin wrapper over the dogstatsd library:

    https://datadogpy.readthedocs.io/en/latest/#datadog-dogstatsd-module

    As such, we directly mirror the public API methods of DogStatsd here; you can refer to the
    DataDog documentation above for how to use this resource.

    Examples:

        .. code-block:: python

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

    '''

    # Mirroring levels from the dogstatsd library
    OK, WARNING, CRITICAL, UNKNOWN = (
        DogStatsd.OK,
        DogStatsd.WARNING,
        DogStatsd.CRITICAL,
        DogStatsd.UNKNOWN,
    )

    def __init__(self, api_key, app_key):
        initialize(api_key=api_key, app_key=app_key)

        # Pull in methods from the dogstatsd library
        for method in [
            'event',
            'gauge',
            'increment',
            'decrement',
            'histogram',
            'distribution',
            'set',
            'service_check',
            'timed',
            'timing',
        ]:
            setattr(self, method, getattr(statsd, method))


@resource(
    {
        'api_key': Field(str, description='Datadog API key'),
        'app_key': Field(str, description='Datadog application key'),
    },
    description='This resource is for publishing to DataDog',
)
def datadog_resource(context):
    return DataDogResource(
        context.resource_config.get('api_key'), context.resource_config.get('app_key')
    )
