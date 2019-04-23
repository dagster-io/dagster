from datadog import initialize, statsd, DogStatsd

from dagster import resource, Dict, Field, String


class DataDogResource:
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
    config_field=Field(
        Dict(
            {
                'api_key': Field(String, description='Datadog API key'),
                'app_key': Field(String, description='Datadog application key'),
            }
        )
    ),
    description='This resource is for publishing to DataDog',
)
def datadog_resource(context):
    return DataDogResource(
        context.resource_config.get('api_key'), context.resource_config.get('app_key')
    )
