import datetime

from dagster import daily_schedule, repository

from .final_pipeline import gcp_pipeline


def define_schedule():
    @daily_schedule(
        pipeline_name="gcp_pipeline",
        start_date=datetime.datetime(2020, 1, 1),
    )
    def explore_visits_daily_schedule(date):
        return {
            "resources": {
                "dataproc": {
                    "config": {
                        "clusterName": "gcp-data-platform",
                        "projectId": "<<PROJECT ID HERE>>",
                        "region": "us-west1",
                    }
                }
            },
            "solids": {
                "bq_load_events": {
                    "config": {"date": date.strftime("%Y/%m/%d"), "table": "events.events"}
                },
                "events_dataproc": {
                    "config": {
                        "cluster_name": "gcp-data-platform",
                        "date": date.strftime("%Y/%m/%d"),
                    }
                },
                "explore_visits_by_hour": {
                    "config": {"table": "aggregations.explore_visits_per_hour"}
                },
            },
        }

    return [explore_visits_daily_schedule]


@repository
def gcp_repo():
    return [gcp_pipeline] + define_schedule()
