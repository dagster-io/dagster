import datetime

from dagster import daily_schedule, repository
from dagster._legacy import pipeline, solid


@solid(config_schema={"date": str})
def do_something_with_config(context):
    return context.solid_config["date"]


@pipeline
def do_it_all():
    do_something_with_config()


@daily_schedule(pipeline_name="do_it_all", start_date=datetime.datetime(2020, 1, 1))
def do_it_all_schedule(date):
    return {
        "solids": {
            "do_something_with_config": {
                "config": {"date": date.strftime("%Y-%m-%d %H")}
            }
        }
    }


@repository
def do_it_all_repo():
    return [do_it_all, do_it_all_schedule]
