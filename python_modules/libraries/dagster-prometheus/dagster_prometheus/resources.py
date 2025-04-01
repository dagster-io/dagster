import prometheus_client
from dagster import ConfigurableResource, resource
from dagster._annotations import beta
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from dagster._core.execution.context.init import InitResourceContext
from prometheus_client.exposition import default_handler
from pydantic import Field, PrivateAttr


class PrometheusClient:
    """Integrates with Prometheus via the prometheus_client library."""


@beta
class PrometheusResource(ConfigurableResource):
    """This resource is used to send metrics to a Prometheus Pushgateway.

    **Example:**

    .. code-block:: python

        from dagster_prometheus import PrometheusResource
        from dagster import Definitions, job, op

        @op
        def example_prometheus_op(prometheus: PrometheusResource):
            prometheus.push_to_gateway(job="my_job")

        @job
        def my_job():
            example_prometheus_op()

        defs = Definitions(
            jobs=[my_job],
            resources={"prometheus": PrometheusResource(gateway="http://pushgateway.local")},
        )

    """

    gateway: str = Field(
        description=(
            "The url for your push gateway. Either of the"
            " form 'http://pushgateway.local', or 'pushgateway.local'."
            " Scheme defaults to 'http' if none is provided"
        )
    )
    timeout: int = Field(
        default=30,
        description="is how long delete will attempt to connect before giving up. Defaults to 30s.",
    )
    _registry: prometheus_client.CollectorRegistry = PrivateAttr(default=None)  # type: ignore

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self._registry = prometheus_client.CollectorRegistry()

    @property
    def registry(self) -> prometheus_client.CollectorRegistry:
        return self._registry

    def push_to_gateway(self, job, grouping_key=None, handler=default_handler) -> None:
        """Push metrics to the given pushgateway.
        `job` is the job label to be attached to all pushed metrics
        `grouping_key` please see the pushgateway documentation for details.
                    Defaults to None
        `handler` is an optional function which can be provided to perform
                requests to the 'gateway'.
                Defaults to None, in which case an http or https request
                will be carried out by a default handler.
                If not None, the argument must be a function which accepts
                the following arguments:
                url, method, timeout, headers, and content
                May be used to implement additional functionality not
                supported by the built-in default handler (such as SSL
                client certicates, and HTTP authentication mechanisms).
                'url' is the URL for the request, the 'gateway' argument
                described earlier will form the basis of this URL.
                'method' is the HTTP method which should be used when
                carrying out the request.
                'timeout' requests not successfully completed after this
                many seconds should be aborted.  If timeout is None, then
                the handler should not set a timeout.
                'headers' is a list of ("header-name","header-value") tuples
                which must be passed to the pushgateway in the form of HTTP
                request headers.
                The function should raise an exception (e.g. IOError) on
                failure.
                'content' is the data which should be used to form the HTTP
                Message Body.
        This overwrites all metrics with the same job and grouping_key.
        This uses the PUT HTTP method.
        """
        prometheus_client.push_to_gateway(
            gateway=self.gateway,
            job=job,
            registry=self._registry,
            grouping_key=grouping_key,
            timeout=self.timeout,
            handler=handler,
        )

    def pushadd_to_gateway(self, job, grouping_key=None, handler=default_handler) -> None:
        """PushAdd metrics to the given pushgateway.
        `job` is the job label to be attached to all pushed metrics
        `registry` is an instance of CollectorRegistry
        `grouping_key` please see the pushgateway documentation for details.
                    Defaults to None
        `handler` is an optional function which can be provided to perform
                requests to the 'gateway'.
                Defaults to None, in which case an http or https request
                will be carried out by a default handler.
                See the 'prometheus_client.push_to_gateway' documentation
                for implementation requirements.
        This replaces metrics with the same name, job and grouping_key.
        This uses the POST HTTP method.
        """
        prometheus_client.pushadd_to_gateway(
            gateway=self.gateway,
            job=job,
            registry=self._registry,
            grouping_key=grouping_key,
            timeout=self.timeout,
            handler=handler,
        )

    def delete_from_gateway(self, job, grouping_key=None, handler=default_handler) -> None:
        """Delete metrics from the given pushgateway.
        `job` is the job label to be attached to all pushed metrics
        `grouping_key` please see the pushgateway documentation for details.
                    Defaults to None
        `handler` is an optional function which can be provided to perform
                requests to the 'gateway'.
                Defaults to None, in which case an http or https request
                will be carried out by a default handler.
                See the 'prometheus_client.push_to_gateway' documentation
                for implementation requirements.
        This deletes metrics with the given job and grouping_key.
        This uses the DELETE HTTP method.
        """
        prometheus_client.delete_from_gateway(
            gateway=self.gateway,
            job=job,
            grouping_key=grouping_key,
            timeout=self.timeout,
            handler=handler,
        )


@beta
@dagster_maintained_resource
@resource(
    config_schema=PrometheusResource.to_config_schema(),
    description="""This resource is for sending metrics to a Prometheus Pushgateway.""",
)
def prometheus_resource(context):
    return PrometheusResource(
        gateway=context.resource_config["gateway"], timeout=context.resource_config["timeout"]
    )
