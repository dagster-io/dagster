from dagster import Field, StringSource, resource
from datadog import DogStatsd, initialize, statsd


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
            "event",
            "gauge",
            "increment",
            "decrement",
            "histogram",
            "distribution",
            "set",
            "service_check",
            "timed",
            "timing",
        ]:
            setattr(self, method, getattr(statsd, method))


@resource(
    {
        "api_key": Field(StringSource, description="Datadog API key"),
        "app_key": Field(StringSource, description="Datadog application key"),
    },
    description="This resource is for publishing to DataDog",
)
def datadog_resource(context):
    """This resource is a thin wrapper over the
    `dogstatsd library <https://datadogpy.readthedocs.io/en/latest/>`_.

    As such, we directly mirror the public API methods of DogStatsd here; you can refer to the
    `DataDog documentation <https://docs.datadoghq.com/developers/dogstatsd/>`_ for how to use this
    resource.

    Examples:
        .. code-block:: python

            @op(required_resource_keys={'datadog'})
            def datadog_op(context):
                dd = context.resources.datadog

                dd.event('Man down!', 'This server needs assistance.')
                dd.gauge('users.online', 1001, tags=["protocol:http"])
                dd.increment('page.views')
                dd.decrement('page.views')
                dd.histogram('album.photo.count', 26, tags=["gender:female"])
                dd.distribution('album.photo.count', 26, tags=["color:blue"])
                dd.set('visitors.uniques', 999, tags=["browser:ie"])
                dd.service_check('svc.check_name', dd.WARNING)
                dd.timing("query.response.time", 1234)

                # Use timed decorator
                @dd.timed('run_fn')
                def run_fn():
                    pass

                run_fn()

            @job(resource_defs={'datadog': datadog_resource})
            def dd_job():
                datadog_op()

            result = dd_job.execute_in_process(
                run_config={'resources': {'datadog': {'config': {'api_key': 'YOUR_KEY', 'app_key': 'YOUR_KEY'}}}}
            )

    """
    return DataDogResource(
        context.resource_config.get("api_key"), context.resource_config.get("app_key")
    )
