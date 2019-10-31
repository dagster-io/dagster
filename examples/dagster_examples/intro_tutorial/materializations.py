import csv
import os

from dagster import (
    EventMetadataEntry,
    Materialization,
    Output,
    execute_pipeline,
    pipeline,
    solid,
)


@solid
def read_csv(context, csv_path):
    with open(csv_path, 'r') as fd:
        lines = [row for row in csv.DictReader(fd)]

    context.log.info('Read {n_lines} lines'.format(n_lines=len(lines)))
    return lines


@solid
def sort_by_calories(context, cereals):
    sorted_cereals = sorted(cereals, key=lambda cereal: cereal['calories'])
    context.log.info(
        'Least caloric cereal: {least_caloric}'.format(
            least_caloric=sorted_cereals[0]['name']
        )
    )
    context.log.info(
        'Most caloric cereal: {most_caloric}'.format(
            most_caloric=sorted_cereals[-1]['name']
        )
    )
    fieldnames = list(sorted_cereals[0].keys())
    sorted_cereals_csv_path = os.path.abspath(
        'calories_sorted_{run_id}.csv'.format(run_id=context.run_id)
    )
    with open(sorted_cereals_csv_path, 'w') as fd:
        writer = csv.DictWriter(fd, fieldnames)
        writer.writeheader()
        writer.writerows(sorted_cereals)
    yield Materialization(
        label='sorted_cereals_csv',
        description='Cereals data frame sorted by caloric content',
        metadata_entries=[
            EventMetadataEntry.path(
                sorted_cereals_csv_path, 'sorted_cereals_csv_path'
            )
        ],
    )
    yield Output(None)


@pipeline
def materialization_pipeline():
    sort_by_calories(read_csv())


if __name__ == '__main__':
    environment_dict = {
        'solids': {
            'read_csv': {'inputs': {'csv_path': {'value': 'cereal.csv'}}}
        }
    }
    result = execute_pipeline(
        materialization_pipeline, environment_dict=environment_dict
    )
    assert result.success
