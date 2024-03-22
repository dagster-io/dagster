from unittest import mock

from dagster import OpExecutionContext, build_op_context, job, op
from dagster_datadog import datadog_resource
from dagster_datadog.resources import DatadogResource


def assert_datadog_client_class(
    datadog_client,
    event,
    gauge,
    increment,
    decrement,
    histogram,
    distribution,
    statsd_set,
    service_check,
    timed,
    timing,
    Event,
    Metric,
    ServiceCheck,
    Metadata,
) -> None:
    datadog_client.event("Man down!", "This server needs assistance.")
    event.assert_called_with("Man down!", "This server needs assistance.")

    # gauge
    datadog_client.gauge("users.online", 1001, tags=["protocol:http"])
    gauge.assert_called_with("users.online", 1001, tags=["protocol:http"])

    # increment
    datadog_client.increment("page.views")
    increment.assert_called_with("page.views")

    # decrement
    datadog_client.decrement("page.views")
    decrement.assert_called_with("page.views")

    datadog_client.histogram("album.photo.count", 26, tags=["gender:female"])
    histogram.assert_called_with("album.photo.count", 26, tags=["gender:female"])

    datadog_client.distribution("album.photo.count", 26, tags=["color:blue"])
    distribution.assert_called_with("album.photo.count", 26, tags=["color:blue"])

    datadog_client.set("visitors.uniques", 999, tags=["browser:ie"])
    statsd_set.assert_called_with("visitors.uniques", 999, tags=["browser:ie"])

    datadog_client.service_check("svc.check_name", datadog_client.WARNING)
    service_check.assert_called_with("svc.check_name", datadog_client.WARNING)

    datadog_client.timing("query.response.time", 1234)
    timing.assert_called_with("query.response.time", 1234)

    datadog_client.api.Event.create(
        title="Something happened!", text="Event text", tags=["version:1", "application:web"]
    )
    Event.create.assert_called_with(
        title="Something happened!", text="Event text", tags=["version:1", "application:web"]
    )

    datadog_client.api.Event.query(
        start=1313769783, end=1419436870, priority="normal", tags=["application:web"]
    )
    Event.query.assert_called_with(
        start=1313769783, end=1419436870, priority="normal", tags=["application:web"]
    )

    datadog_client.api.Metric.send(metric="my.series", points=[(1711113823, 15), (1711113833, 16)])
    Metric.send.assert_called_with(metric="my.series", points=[(1711113823, 15), (1711113833, 16)])

    datadog_client.api.ServiceCheck.check(
        check="app.ok", host_name="127.0.0.1", status=0, tags=["test:ExampleServiceCheck"]
    )
    ServiceCheck.check.assert_called_with(
        check="app.ok", host_name="127.0.0.1", status=0, tags=["test:ExampleServiceCheck"]
    )

    datadog_client.api.Metadata.get(metric_name="my_metric")
    Metadata.get.assert_called_with(metric_name="my_metric")

    @datadog_client.timed("run_fn")
    def run_fn() -> None:
        pass

    run_fn()
    timed.assert_called_with("run_fn")


@mock.patch("datadog.api.Metadata")
@mock.patch("datadog.api.ServiceCheck")
@mock.patch("datadog.api.Metric")
@mock.patch("datadog.api.Event")
@mock.patch("datadog.statsd.timing")
@mock.patch("datadog.statsd.timed")
@mock.patch("datadog.statsd.service_check")
@mock.patch("datadog.statsd.set")
@mock.patch("datadog.statsd.distribution")
@mock.patch("datadog.statsd.histogram")
@mock.patch("datadog.statsd.decrement")
@mock.patch("datadog.statsd.increment")
@mock.patch("datadog.statsd.gauge")
@mock.patch("datadog.statsd.event")
def test_datadog_resource(
    event,
    gauge,
    increment,
    decrement,
    histogram,
    distribution,
    statsd_set,
    service_check,
    timed,
    timing,
    Event,
    Metric,
    ServiceCheck,
    Metadata,
) -> None:
    executed = {}

    @op(required_resource_keys={"datadog"})
    def datadog_op(context: OpExecutionContext):
        assert context.resources.datadog
        assert_datadog_client_class(
            context.resources.datadog,
            event,
            gauge,
            increment,
            decrement,
            histogram,
            distribution,
            statsd_set,
            service_check,
            timed,
            timing,
            Event,
            Metric,
            ServiceCheck,
            Metadata,
        )
        executed["yes"] = True
        return True

    context = build_op_context(
        resources={
            "datadog": datadog_resource.configured({"api_key": "NOT_USED", "app_key": "NOT_USED"})
        }
    )
    assert datadog_op(context)
    assert executed["yes"]


@mock.patch("datadog.api.Metadata")
@mock.patch("datadog.api.ServiceCheck")
@mock.patch("datadog.api.Metric")
@mock.patch("datadog.api.Event")
@mock.patch("datadog.statsd.timing")
@mock.patch("datadog.statsd.timed")
@mock.patch("datadog.statsd.service_check")
@mock.patch("datadog.statsd.set")
@mock.patch("datadog.statsd.distribution")
@mock.patch("datadog.statsd.histogram")
@mock.patch("datadog.statsd.decrement")
@mock.patch("datadog.statsd.increment")
@mock.patch("datadog.statsd.gauge")
@mock.patch("datadog.statsd.event")
def test_datadog_pythonic_resource_standalone_op(
    event,
    gauge,
    increment,
    decrement,
    histogram,
    distribution,
    statsd_set,
    service_check,
    timed,
    timing,
    Event,
    Metric,
    ServiceCheck,
    Metadata,
) -> None:
    executed = {}

    @op
    def datadog_op(datadog_resource: DatadogResource):
        datadog_client = datadog_resource.get_client()
        assert datadog_client
        assert_datadog_client_class(
            datadog_client,
            event,
            gauge,
            increment,
            decrement,
            histogram,
            distribution,
            statsd_set,
            service_check,
            timed,
            timing,
            Event,
            Metric,
            ServiceCheck,
            Metadata,
        )
        executed["yes"] = True
        return True

    # https://github.com/dagster-io/dagster/issues/13384
    # assert datadog_op(DatadogClient(api_key="NOT_USED", app_key="NOT_USED")) # does not work
    assert datadog_op(datadog_resource=DatadogResource(api_key="NOT_USED", app_key="NOT_USED"))
    assert executed["yes"]


@mock.patch("datadog.api.Metadata")
@mock.patch("datadog.api.ServiceCheck")
@mock.patch("datadog.api.Metric")
@mock.patch("datadog.api.Event")
@mock.patch("datadog.statsd.timing")
@mock.patch("datadog.statsd.timed")
@mock.patch("datadog.statsd.service_check")
@mock.patch("datadog.statsd.set")
@mock.patch("datadog.statsd.distribution")
@mock.patch("datadog.statsd.histogram")
@mock.patch("datadog.statsd.decrement")
@mock.patch("datadog.statsd.increment")
@mock.patch("datadog.statsd.gauge")
@mock.patch("datadog.statsd.event")
def test_datadog_pythonic_resource_factory_op_in_job(
    event,
    gauge,
    increment,
    decrement,
    histogram,
    distribution,
    statsd_set,
    service_check,
    timed,
    timing,
    Event,
    Metric,
    ServiceCheck,
    Metadata,
) -> None:
    executed = {}

    @op
    def datadog_op(datadog_resource: DatadogResource):
        datadog_client = datadog_resource.get_client()
        assert datadog_client
        assert datadog_client.api_key == "FOO"
        assert datadog_client.app_key == "BAR"
        assert_datadog_client_class(
            datadog_client,
            event,
            gauge,
            increment,
            decrement,
            histogram,
            distribution,
            statsd_set,
            service_check,
            timed,
            timing,
            Event,
            Metric,
            ServiceCheck,
            Metadata,
        )
        executed["yes"] = True
        return True

    @job
    def job_for_datadog_op() -> None:
        datadog_op()

    job_for_datadog_op.execute_in_process(
        resources={"datadog_resource": DatadogResource(api_key="FOO", app_key="BAR")}
    )

    assert executed["yes"]
