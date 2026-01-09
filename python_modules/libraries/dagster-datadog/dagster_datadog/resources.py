from typing import Optional

from dagster import ConfigurableResource, resource
from dagster._annotations import beta
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from datadog import DogStatsd, api, initialize, statsd
from pydantic import Field


class DatadogClient:
    # Mirroring levels from the dogstatsd library
    OK, WARNING, CRITICAL, UNKNOWN = (
        DogStatsd.OK,
        DogStatsd.WARNING,
        DogStatsd.CRITICAL,
        DogStatsd.UNKNOWN,
    )

    def __init__(
        self,
        api_key: Optional[str],
        app_key: Optional[str],
        host_name: Optional[str] = None,
        api_host: Optional[str] = None,
        statsd_host: Optional[str] = None,
        statsd_port: Optional[int] = None,
        statsd_disable_aggregation: bool = True,
        statsd_disable_buffering: bool = True,
        statsd_aggregation_flush_interval: float = 0.3,
        statsd_use_default_route: bool = False,
        statsd_socket_path: Optional[str] = None,
        statsd_namespace: Optional[str] = None,
        statsd_max_samples_per_context: Optional[int] = 0,
        statsd_constant_tags: Optional[list[str]] = None,
        return_raw_response: bool = False,
        hostname_from_config: bool = True,
        cardinality: Optional[str] = None,
    ):
        self.api_key = api_key
        self.app_key = app_key
        initialize(
            api_key=api_key,
            app_key=app_key,
            host_name=host_name,
            api_host=api_host,
            statsd_host=statsd_host,
            statsd_port=statsd_port,
            statsd_disable_aggregation=statsd_disable_aggregation,
            statsd_disable_buffering=statsd_disable_buffering,
            statsd_aggregation_flush_interval=statsd_aggregation_flush_interval,
            statsd_use_default_route=statsd_use_default_route,
            statsd_socket_path=statsd_socket_path,
            statsd_namespace=statsd_namespace,
            statsd_max_samples_per_context=statsd_max_samples_per_context,
            statsd_constant_tags=statsd_constant_tags,
            return_raw_response=return_raw_response,
            hostname_from_config=hostname_from_config,
            cardinality=cardinality,
        )

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
            "flush",
            "wait_for_pending",
        ]:
            setattr(self, method, getattr(statsd, method))

        self.api = api


@beta
class DatadogResource(ConfigurableResource):
    """This resource is a thin wrapper over the
    `dogstatsd library <https://datadogpy.readthedocs.io/en/latest/>`_.

    As such, we directly mirror the public API methods of DogStatsd here; you can refer to the
    `Datadog documentation <https://docs.datadoghq.com/developers/dogstatsd/>`_ for how to use this
    resource.

    Examples:
        .. code-block:: python

            @op
            def datadog_op(datadog_resource: DatadogResource):
                datadog_client = datadog_resource.get_client()
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
                resources={"datadog_resource": DatadogResource(api_key="FOO", app_key="BAR")}
            )

    """

    api_key: str = Field(
        description=(
            "Datadog API key. See https://docs.datadoghq.com/account_management/api-app-keys/"
        )
    )
    app_key: str = Field(
        description=(
            "Datadog application key. See"
            " https://docs.datadoghq.com/account_management/api-app-keys/."
        )
    )
    host_name: Optional[str] = None
    api_host: Optional[str] = None
    statsd_host: Optional[str] = None
    statsd_port: Optional[int] = None
    statsd_disable_aggregation: bool = True
    statsd_disable_buffering: bool = True
    statsd_aggregation_flush_interval: float = 0.3
    statsd_use_default_route: bool = False
    statsd_socket_path: Optional[str] = None
    statsd_namespace: Optional[str] = None
    statsd_max_samples_per_context: Optional[int] = 0
    statsd_constant_tags: Optional[list[str]] = None
    return_raw_response: bool = False
    hostname_from_config: bool = True
    cardinality: Optional[str] = None

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def get_client(self) -> DatadogClient:
        return DatadogClient(
            api_key=self.api_key,
            app_key=self.app_key,
            host_name=self.host_name,
            api_host=self.api_host,
            statsd_host=self.statsd_host,
            statsd_port=self.statsd_port,
            statsd_disable_aggregation=self.statsd_disable_aggregation,
            statsd_disable_buffering=self.statsd_disable_buffering,
            statsd_aggregation_flush_interval=self.statsd_aggregation_flush_interval,
            statsd_use_default_route=self.statsd_use_default_route,
            statsd_socket_path=self.statsd_socket_path,
            statsd_namespace=self.statsd_namespace,
            statsd_max_samples_per_context=self.statsd_max_samples_per_context,
            statsd_constant_tags=self.statsd_constant_tags,
            return_raw_response=self.return_raw_response,
            hostname_from_config=self.hostname_from_config,
            cardinality=self.cardinality,
        )


@beta
@dagster_maintained_resource
@resource(
    config_schema=DatadogResource.to_config_schema(),
    description="This resource is for publishing to DataDog",
)
def datadog_resource(context) -> DatadogClient:
    """This legacy resource is a thin wrapper over the
    `dogstatsd library <https://datadogpy.readthedocs.io/en/latest/>`_.

    Prefer using :py:class:`DatadogResource`.

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
    return DatadogResource.from_resource_context(context).get_client()
