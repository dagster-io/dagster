# start_scheduler_marker_0
import csv
from datetime import datetime, time

import requests
from dagster import daily_schedule, pipeline, repository, solid


@solid
def hello_cereal(context):
    response = requests.get("https://docs.dagster.io/assets/cereal.csv")
    lines = response.text.split("\n")
    cereals = [row for row in csv.DictReader(lines)]
    date = context.solid_config["date"]
    context.log.info(f"Today is {date}. Found {len(cereals)} cereals.")


@pipeline
def hello_cereal_pipeline():
    hello_cereal()


# end_scheduler_marker_0

# start_scheduler_marker_1
@daily_schedule(
    pipeline_name="hello_cereal_pipeline",
    start_date=datetime(2020, 6, 1),
    execution_time=time(6, 45),
    execution_timezone="US/Central",
)
def good_morning_schedule(date):
    return {
        "solids": {
            "hello_cereal": {"config": {"date": date.strftime("%Y-%m-%d")}}
        }
    }


# end_scheduler_marker_1

# start_scheduler_marker_2
@repository
def hello_cereal_repository():
    return [hello_cereal_pipeline, good_morning_schedule]


# end_scheduler_marker_2

# start_scheduler_marker_3
def weekday_filter(_context):
    weekno = datetime.today().weekday()
    # Returns true if current day is a weekday
    return weekno < 5


# end_scheduler_marker_3

# start_scheduler_marker_4
@daily_schedule(
    pipeline_name="hello_cereal_pipeline",
    start_date=datetime(2020, 6, 1),
    execution_time=time(6, 45),
    execution_timezone="US/Central",
    should_execute=weekday_filter,
)
def good_weekday_morning_schedule(date):
    return {
        "solids": {
            "hello_cereal": {
                "inputs": {"date": {"value": date.strftime("%Y-%m-%d")}}
            }
        }
    }


# end_scheduler_marker_4
