import time

from dagster import ModeDefinition, execute_solid, solid
from dagster_prometheus import prometheus_resource
from prometheus_client import Counter, Enum, Gauge, Histogram, Info, Summary

EPS = 0.001
ENV = {"resources": {"prometheus": {"config": {"gateway": "localhost:9091"}}}}
MODE = ModeDefinition(resource_defs={"prometheus": prometheus_resource})


def test_prometheus_counter():
    @solid(required_resource_keys={"prometheus"})
    def prometheus_solid(context):
        c = Counter(
            "some_counter_seconds",
            "Description of this counter",
            registry=context.resources.prometheus.registry,
        )
        c.inc()
        c.inc(1.6)
        recorded = context.resources.prometheus.registry.get_sample_value(
            "some_counter_seconds_total"
        )
        assert abs(2.6 - recorded) < EPS

    assert execute_solid(prometheus_solid, run_config=ENV, mode_def=MODE).success


def test_prometheus_gauge():
    @solid(required_resource_keys={"prometheus"})
    def prometheus_solid(context):
        g = Gauge(
            "job_last_success_unixtime",
            "Last time a batch job successfully finished",
            registry=context.resources.prometheus.registry,
        )
        g.set_to_current_time()
        recorded = context.resources.prometheus.registry.get_sample_value(
            "job_last_success_unixtime"
        )
        assert abs(time.time() - recorded) < 10.0

    assert execute_solid(prometheus_solid, run_config=ENV, mode_def=MODE).success


def test_prometheus_summary():
    @solid(required_resource_keys={"prometheus"})
    def prometheus_solid(context):
        s = Summary(
            "request_latency_seconds",
            "Description of summary",
            registry=context.resources.prometheus.registry,
        )
        s.observe(4.7)
        request_time = Summary(
            "response_latency_seconds",
            "Response latency (seconds)",
            registry=context.resources.prometheus.registry,
        )

        with request_time.time():
            time.sleep(1)

        recorded = context.resources.prometheus.registry.get_sample_value(
            "request_latency_seconds_sum"
        )
        assert abs(4.7 - recorded) < EPS

        recorded = context.resources.prometheus.registry.get_sample_value(
            "response_latency_seconds_sum"
        )
        assert abs(1.0 - recorded) < 1.0

    assert execute_solid(prometheus_solid, run_config=ENV, mode_def=MODE).success


def test_prometheus_histogram():
    @solid(required_resource_keys={"prometheus"})
    def prometheus_solid(context):
        h = Histogram(
            "pipeline_runtime_seconds",
            "Description of histogram",
            registry=context.resources.prometheus.registry,
        )
        h.observe(4.7)
        recorded = context.resources.prometheus.registry.get_sample_value(
            "pipeline_runtime_seconds_sum"
        )
        assert abs(4.7 - recorded) < EPS

    assert execute_solid(prometheus_solid, run_config=ENV, mode_def=MODE).success


def test_prometheus_info():
    @solid(required_resource_keys={"prometheus"})
    def prometheus_solid(context):
        i = Info(
            "my_build_version",
            "Description of info",
            registry=context.resources.prometheus.registry,
        )
        info_labels = {"version": "1.2.3", "buildhost": "foo@bar"}
        i.info(info_labels)
        metric = None
        for metric in context.resources.prometheus.registry.collect():
            if metric.name == "my_build_version":
                break
        assert metric and metric.samples[0].labels == info_labels

    assert execute_solid(prometheus_solid, run_config=ENV, mode_def=MODE).success


def test_prometheus_enum():
    @solid(required_resource_keys={"prometheus"})
    def prometheus_solid(context):
        e = Enum(
            "my_task_state",
            "Description of enum",
            states=["starting", "running", "stopped"],
            registry=context.resources.prometheus.registry,
        )
        # no idea why pylint doesn't like this line, it's correct
        e.state("running")  # pylint: disable=no-member

        metric = None
        for metric in context.resources.prometheus.registry.collect():
            if metric.name == "my_task_state":
                break
        assert metric and metric.samples[0].labels == {"my_task_state": "starting"}

    assert execute_solid(prometheus_solid, run_config=ENV, mode_def=MODE).success
