import prometheus_client
from dagster import Field, check, resource
from prometheus_client.exposition import default_handler


class PrometheusResource:
    """Integrates with Prometheus via the prometheus_client library.
    """

    def __init__(self, gateway, timeout):
        self.gateway = check.str_param(gateway, "gateway")
        self.timeout = check.opt_int_param(timeout, "timeout")
        self.registry = prometheus_client.CollectorRegistry()

    def push_to_gateway(self, job, grouping_key=None, handler=default_handler):
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
        This uses the PUT HTTP method."""
        prometheus_client.push_to_gateway(
            gateway=self.gateway,
            job=job,
            registry=self.registry,
            grouping_key=grouping_key,
            timeout=self.timeout,
            handler=handler,
        )

    def pushadd_to_gateway(self, job, grouping_key=None, handler=default_handler):
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
        This uses the POST HTTP method."""
        prometheus_client.pushadd_to_gateway(
            gateway=self.gateway,
            job=job,
            registry=self.registry,
            grouping_key=grouping_key,
            timeout=self.timeout,
            handler=handler,
        )

    def delete_from_gateway(self, job, grouping_key=None, handler=default_handler):
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
        This uses the DELETE HTTP method."""
        prometheus_client.delete_from_gateway(
            gateway=self.gateway,
            job=job,
            grouping_key=grouping_key,
            timeout=self.timeout,
            handler=handler,
        )


@resource(
    {
        "gateway": Field(
            str,
            description="the url for your push gateway. Either of the form "
            "'http://pushgateway.local', or 'pushgateway.local'. "
            "Scheme defaults to 'http' if none is provided",
        ),
        "timeout": Field(
            int,
            default_value=30,
            is_required=False,
            description="is how long delete will attempt to connect before giving up. "
            "Defaults to 30s.",
        ),
    },
    description="""This resource is for sending metrics to a Prometheus Pushgateway.""",
)
def prometheus_resource(context):
    return PrometheusResource(
        gateway=context.resource_config["gateway"], timeout=context.resource_config["timeout"]
    )
