import dagster as dg
from dagster_prometheus import PrometheusResource
from prometheus_client import REGISTRY, Counter, Histogram, push_to_gateway


# start_basic_prometheus_asset
@dg.asset
def prometheus_metric(context, prometheus: PrometheusResource):
    prometheus.push_to_gateway(job="my_job_label")


# end_basic_prometheus_asset

# start_custom_metrics_setup
my_asset_runs_total = Counter("my_asset_runs_total", "Total runs of my asset")
my_asset_success_total = Counter("my_asset_success_total", "Total successful runs")
my_asset_failure_total = Counter("my_asset_failure_total", "Total failed runs")
my_asset_duration_seconds = Histogram(
    "my_asset_duration_seconds", "Duration of asset runs in seconds"
)
# end_custom_metrics_setup


# start_custom_prometheus_asset
@dg.asset
def custom_prometheus_asset(context, prometheus: PrometheusResource):
    my_asset_runs_total.inc()

    with my_asset_duration_seconds.time():
        try:
            # ... your asset logic ...
            my_asset_success_total.inc()
        except Exception:
            my_asset_failure_total.inc()
            raise
        finally:
            # Push metrics to the gateway
            push_to_gateway(
                prometheus.gateway,
                job="my_job_label",
                registry=REGISTRY,
            )


# end_custom_prometheus_asset
