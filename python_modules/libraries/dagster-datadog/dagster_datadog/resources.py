from datadog import DogStatsd, initialize, statsd

from dagster import Field, resource


class DataDogResource(object):
    '''DataDogResource

    This resource is a thin wrapper over the dogstatsd library:

    https://datadogpy.readthedocs.io/en/latest/#datadog-dogstatsd-module

    As such, we directly mirror the public API methods of DogStatsd here; you can refer to the
    DataDog documentation above for how to use this resource.
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
