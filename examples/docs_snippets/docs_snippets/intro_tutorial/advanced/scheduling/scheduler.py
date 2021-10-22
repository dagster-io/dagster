# start_scheduler_marker_0
import csv
from datetime import datetime

import requests
from dagster import job, op, repository, schedule


@op
def hello_cereal(context):
    response = requests.get("https://docs.dagster.io/assets/cereal.csv")
    lines = response.text.split("\n")
    cereals = [row for row in csv.DictReader(lines)]
    date = context.op_config["date"]
    context.log.info(f"Today is {date}. Found {len(cereals)} cereals.")


@job
def hello_cereal_job():
    hello_cereal()


# end_scheduler_marker_0

# start_scheduler_marker_1
@schedule(
    cron_schedule="45 6 * * *",
    job=hello_cereal_job,
    execution_timezone="US/Central",
)
def good_morning_schedule(context):
    date = context.scheduled_execution_time.strftime("%Y-%m-%d")
    return {"ops": {"hello_cereal": {"config": {"date": date}}}}


# end_scheduler_marker_1

# start_scheduler_marker_2
@repository
def hello_cereal_repository():
    return [hello_cereal_job, good_morning_schedule]


# end_scheduler_marker_2

# start_scheduler_marker_3
def weekday_filter(_context):
    weekno = datetime.today().weekday()
    # Returns true if current day is a weekday
    return weekno < 5


# end_scheduler_marker_3

# start_scheduler_marker_4
@schedule(
    cron_schedule="45 6 * * *",
    job=hello_cereal_job,
    execution_timezone="US/Central",
    should_execute=weekday_filter,
)
def good_weekday_morning_schedule(context):
    date = context.scheduled_execution_time.strftime("%Y-%m-%d")
    return {"ops": {"hello_cereal": {"inputs": {"date": {"value": date}}}}}


# end_scheduler_marker_4
