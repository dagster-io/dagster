import csv
from datetime import datetime, time

from dagster import daily_schedule, pipeline, repository, solid
from dagster.utils import file_relative_path


@solid
def hello_cereal(context, date):
    dataset_path = file_relative_path(__file__, "cereal.csv")
    context.log.info(dataset_path)
    with open(dataset_path, "r") as fd:
        cereals = [row for row in csv.DictReader(fd)]

    context.log.info(
        "Today is {date}. Found {n_cereals} cereals".format(
            date=date, n_cereals=len(cereals)
        )
    )


@pipeline
def hello_cereal_pipeline():
    hello_cereal()


@daily_schedule(
    pipeline_name="hello_cereal_pipeline",
    start_date=datetime(2020, 6, 1),
    execution_time=time(6, 45),
)
def good_morning_schedule(date):
    return {
        "solids": {
            "hello_cereal": {
                "inputs": {"date": {"value": date.strftime("%Y-%m-%d")}}
            }
        }
    }


@repository
def hello_cereal_repository():
    return [hello_cereal_pipeline, good_morning_schedule]


def weekday_filter():
    weekno = datetime.today().weekday()
    # Returns true if current day is a weekday
    return weekno < 5


@daily_schedule(
    pipeline_name="hello_cereal_pipeline",
    start_date=datetime(2020, 6, 1),
    execution_time=time(6, 45),
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
