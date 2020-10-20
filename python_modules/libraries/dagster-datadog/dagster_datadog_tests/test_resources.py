from dagster import ModeDefinition, execute_solid, solid
from dagster.seven import mock
from dagster_datadog import datadog_resource


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
):
    @solid(required_resource_keys={"datadog"})
    def datadog_solid(context):
        assert context.resources.datadog

        # event
        context.resources.datadog.event("Man down!", "This server needs assistance.")
        event.assert_called_with("Man down!", "This server needs assistance.")

        # gauge
        context.resources.datadog.gauge("users.online", 1001, tags=["protocol:http"])
        gauge.assert_called_with("users.online", 1001, tags=["protocol:http"])

        # increment
        context.resources.datadog.increment("page.views")
        increment.assert_called_with("page.views")

        # decrement
        context.resources.datadog.decrement("page.views")
        decrement.assert_called_with("page.views")

        context.resources.datadog.histogram("album.photo.count", 26, tags=["gender:female"])
        histogram.assert_called_with("album.photo.count", 26, tags=["gender:female"])

        context.resources.datadog.distribution("album.photo.count", 26, tags=["color:blue"])
        distribution.assert_called_with("album.photo.count", 26, tags=["color:blue"])

        context.resources.datadog.set("visitors.uniques", 999, tags=["browser:ie"])
        statsd_set.assert_called_with("visitors.uniques", 999, tags=["browser:ie"])

        context.resources.datadog.service_check("svc.check_name", context.resources.datadog.WARNING)
        service_check.assert_called_with("svc.check_name", context.resources.datadog.WARNING)

        context.resources.datadog.timing("query.response.time", 1234)
        timing.assert_called_with("query.response.time", 1234)

        @context.resources.datadog.timed("run_fn")
        def run_fn():
            pass

        run_fn()
        timed.assert_called_with("run_fn")

    result = execute_solid(
        datadog_solid,
        run_config={
            "resources": {"datadog": {"config": {"api_key": "NOT_USED", "app_key": "NOT_USED"}}}
        },
        mode_def=ModeDefinition(resource_defs={"datadog": datadog_resource}),
    )
    assert result.success
