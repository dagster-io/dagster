from dagster_prometheus import PrometheusResource

import dagster as dg


@dg.asset
def prometheus_metric(prometheus: PrometheusResource):
    prometheus.push_to_gateway(job="my_job_label")


defs = dg.Definitions(
    assets=[prometheus_metric],
    resources={
        "prometheus": PrometheusResource(gateway="http://pushgateway.example.org:9091")
    },
)
