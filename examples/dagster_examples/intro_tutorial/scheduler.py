import csv

from dagster import ScheduleDefinition, pipeline, repository, solid
from dagster.utils import file_relative_path


@solid
def hello_cereal(context):
    dataset_path = file_relative_path(__file__, "cereal.csv")
    context.log.info(dataset_path)
    with open(dataset_path, 'r') as fd:
        cereals = [row for row in csv.DictReader(fd)]

    context.log.info(
        'Found {n_cereals} cereals'.format(n_cereals=len(cereals))
    )


@pipeline
def hello_cereal_pipeline():
    hello_cereal()


def cereal_schedules():
    return [
        ScheduleDefinition(
            name='good_morning',
            cron_schedule='45 6 * * *',
            pipeline_name='hello_cereal_pipeline',
            run_config={'storage': {'filesystem': {}}},
        )
    ]


@repository
def hello_cereal_repository():
    return [hello_cereal_pipeline] + cereal_schedules()
