from dagster import ConfigurableResourceFactory, resource
from dagster._config.structured_config import infer_schema_from_config_class
from datadog import DogStatsd, initialize, statsd
from pydantic import Field


class DataDogClient:
    # Mirroring levels from the dogstatsd library
    OK, WARNING, CRITICAL, UNKNOWN = (
        DogStatsd.OK,
        DogStatsd.WARNING,
        DogStatsd.CRITICAL,
        DogStatsd.UNKNOWN,
    )

    def __init__(self, api_key: str, app_key: str):
        self.api_key = api_key
        self.app_key = app_key
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


class DataDogClientResource(ConfigurableResourceFactory[DataDogClient]):
    """This resource is a thin wrapper over the
    `dogstatsd library <https://datadogpy.readthedocs.io/en/latest/>`_.

    As such, we directly mirror the public API methods of DogStatsd here; you can refer to the
    `DataDog documentation <https://docs.datadoghq.com/developers/dogstatsd/>`_ for how to use this
    resource.

    Examples:
        .. code-block:: python

            @op
            def datadog_op(datadog_client: Resource[DataDogClient]):
                datadog_client.event('Man down!', 'This server needs assistance.')
                datadog_client.gauge('users.online', 1001, tags=["protocol:http"])
                datadog_client.increment('page.views')
                datadog_client.decrement('page.views')
                datadog_client.histogram('album.photo.count', 26, tags=["gender:female"])
                datadog_client.distribution('album.photo.count', 26, tags=["color:blue"])
                datadog_client.set('visitors.uniques', 999, tags=["browser:ie"])
                datadog_client.service_check('svc.check_name', datadog_client.WARNING)
                datadog_client.timing("query.response.time", 1234)

                # Use timed decorator
                @datadog_client.timed('run_fn')
                def run_fn():
                    pass

                run_fn()

            @job
            def job_for_datadog_op() -> None:
                datadog_op()

            job_for_datadog_op.execute_in_process(
                resources={"datadog_client": DataDogClientResource(api_key="FOO", app_key="BAR")}
            )

    """

    api_key: str = Field(description="Datadog API key")
    app_key: str = Field(description="Datadog application key")

    def create_resource(self, _init_context) -> DataDogClient:
        return DataDogClient(self.api_key, self.app_key)


@resource(
    config_schema=DataDogClientResource.to_config_schema(),
    description="This resource is for publishing to DataDog",
)
def datadog_resource(context) -> DataDogClient:
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
    return DataDogClientResource.from_resource_context(context)
