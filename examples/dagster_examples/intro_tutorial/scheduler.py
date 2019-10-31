import csv

from dagster_cron import SystemCronScheduler

from dagster import (
    RepositoryDefinition,
    ScheduleDefinition,
    execute_pipeline,
    pipeline,
    schedules,
    solid,
)


@solid
def scheduled_cereal(context):
    dataset_path = 'cereal.csv'
    with open(dataset_path, 'r') as fd:
        cereals = [row for row in csv.DictReader(fd)]

    context.log.info(
        'Found {n_cereals} cereals'.format(n_cereals=len(cereals))
    )


@pipeline
def scheduled_cereal_pipeline():
    scheduled_cereal()


def scheduled_cereal_repository():
    return RepositoryDefinition(
        'scheduled_cereal', pipeline_defs=[scheduled_cereal_pipeline]
    )


@schedules(SystemCronScheduler)
def cereal_schedules():
    return [
        ScheduleDefinition(
            name='good_morning',
            cron_schedule='45 6 * * *',
            pipeline_name='scheduled_cereal_pipeline',
            environment_dict={'storage': {'filesystem': {}}},
        )
    ]


if __name__ == '__main__':
    result = execute_pipeline(scheduled_cereal_pipeline)
    assert result.success
