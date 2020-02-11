import csv

from dagster import DagsterType, execute_pipeline, pipeline, solid

SimpleDataFrame = DagsterType(
    name='SimpleDataFrame',
    type_check_fn=lambda _, value: isinstance(value, list),
    description='A naive representation of a data frame, e.g., as returned by csv.DictReader.',
)


@solid
def read_csv(context, csv_path: str) -> SimpleDataFrame:
    with open(csv_path, 'r') as fd:
        lines = [row for row in csv.DictReader(fd)]

    context.log.info('Read {n_lines} lines'.format(n_lines=len(lines)))
    return lines


@solid
def sort_by_calories(context, cereals: SimpleDataFrame):
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


@pipeline
def custom_type_pipeline():
    sort_by_calories(read_csv())


if __name__ == '__main__':
    environment_dict = {
        'solids': {
            'read_csv': {'inputs': {'csv_path': {'value': 'cereal.csv'}}}
        }
    }
    result = execute_pipeline(
        custom_type_pipeline, environment_dict=environment_dict
    )
    assert result.success
