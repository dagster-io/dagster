import dagster as dg
from dagster_prometheus import PrometheusResource


# start_prometheus_resources
@dg.definitions
def resources():
    return dg.Definitions(
        resources={
            "prometheus": PrometheusResource(
                gateway="http://pushgateway.example.org:9091",
                job_name="dagster",
                scrape_interval="10s",
                scrape_timeout="10s",
                evaluation_interval="10s",
            )
        }
    )


# end_prometheus_resources
