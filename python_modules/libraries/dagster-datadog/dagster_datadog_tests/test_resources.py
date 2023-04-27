from unittest import mock

from dagster import OpExecutionContext, build_op_context, job, op
from dagster_datadog import datadog_resource
from dagster_datadog.resources import DatadogResource


def assert_datadog_resource_class(
    datadog_resource,
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
) -> None:
    datadog_resource.event("Man down!", "This server needs assistance.")
    event.assert_called_with("Man down!", "This server needs assistance.")

    # gauge
    datadog_resource.gauge("users.online", 1001, tags=["protocol:http"])
    gauge.assert_called_with("users.online", 1001, tags=["protocol:http"])

    # increment
    datadog_resource.increment("page.views")
    increment.assert_called_with("page.views")

    # decrement
    datadog_resource.decrement("page.views")
    decrement.assert_called_with("page.views")

    datadog_resource.histogram("album.photo.count", 26, tags=["gender:female"])
    histogram.assert_called_with("album.photo.count", 26, tags=["gender:female"])

    datadog_resource.distribution("album.photo.count", 26, tags=["color:blue"])
    distribution.assert_called_with("album.photo.count", 26, tags=["color:blue"])

    datadog_resource.set("visitors.uniques", 999, tags=["browser:ie"])
    statsd_set.assert_called_with("visitors.uniques", 999, tags=["browser:ie"])

    datadog_resource.service_check("svc.check_name", datadog_resource.WARNING)
    service_check.assert_called_with("svc.check_name", datadog_resource.WARNING)

    datadog_resource.timing("query.response.time", 1234)
    timing.assert_called_with("query.response.time", 1234)

    @datadog_resource.timed("run_fn")
    def run_fn() -> None:
        pass

    run_fn()
    timed.assert_called_with("run_fn")


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
) -> None:
    executed = {}

    @op(required_resource_keys={"datadog"})
    def datadog_op(context: OpExecutionContext):
        assert context.resources.datadog
        assert_datadog_resource_class(
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
) -> None:
    executed = {}

    @op
    def datadog_op(datadog_resource: DatadogResource):
        assert datadog_resource
        assert_datadog_resource_class(
            datadog_resource,
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
        )
        executed["yes"] = True
        return True

    assert datadog_op(DatadogResource(api_key="NOT_USED", app_key="NOT_USED"))
    assert executed["yes"]


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
) -> None:
    executed = {}

    @op
    def datadog_op(datadog_resource: DatadogResource):
        assert datadog_resource
        assert datadog_resource.api_key == "FOO"
        assert datadog_resource.app_key == "BAR"
        assert_datadog_resource_class(
            datadog_resource,
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
