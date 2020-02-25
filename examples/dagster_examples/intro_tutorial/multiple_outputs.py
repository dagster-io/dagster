import csv
import typing

from dagster import (
    Bool,
    Field,
    Output,
    OutputDefinition,
    PythonObjectDagsterType,
    execute_pipeline,
    pipeline,
    solid,
)

if typing.TYPE_CHECKING:
    DataFrame = list
else:
    DataFrame = PythonObjectDagsterType(list, name='DataFrame')  # type: Any


@solid
def read_csv(context, csv_path):
    with open(csv_path, 'r') as fd:
        lines = [row for row in csv.DictReader(fd)]

    context.log.info('Read {n_lines} lines'.format(n_lines=len(lines)))
    return lines


@solid(
    config={
        'process_hot': Field(Bool, is_required=False, default_value=True),
        'process_cold': Field(Bool, is_required=False, default_value=True),
    },
    output_defs=[
        OutputDefinition(
            name='hot_cereals', dagster_type=DataFrame, is_required=False
        ),
        OutputDefinition(
            name='cold_cereals', dagster_type=DataFrame, is_required=False
        ),
    ],
)
def split_cereals(context, cereals):
    if context.solid_config['process_hot']:
        hot_cereals = [cereal for cereal in cereals if cereal['type'] == 'H']
        yield Output(hot_cereals, 'hot_cereals')
    if context.solid_config['process_cold']:
        cold_cereals = [cereal for cereal in cereals if cereal['type'] == 'C']
        yield Output(cold_cereals, 'cold_cereals')


@solid
def sort_hot_cereals_by_calories(context, cereals):
    sorted_cereals = sorted(cereals, key=lambda cereal: cereal['calories'])
    context.log.info(
        'Least caloric hot cereal: {least_caloric}'.format(
            least_caloric=sorted_cereals[0]['name']
        )
    )


@solid
def sort_cold_cereals_by_calories(context, cereals):
    sorted_cereals = sorted(cereals, key=lambda cereal: cereal['calories'])
    context.log.info(
        'Least caloric cold cereal: {least_caloric}'.format(
            least_caloric=sorted_cereals[0]['name']
        )
    )


@pipeline
def multiple_outputs_pipeline():
    hot_cereals, cold_cereals = split_cereals(read_csv())
    sort_hot_cereals_by_calories(hot_cereals)
    sort_cold_cereals_by_calories(cold_cereals)


if __name__ == '__main__':
    environment_dict = {
        'solids': {
            'read_csv': {'inputs': {'csv_path': {'value': 'cereal.csv'}}}
        }
    }
    result = execute_pipeline(
        multiple_outputs_pipeline, environment_dict=environment_dict
    )
    assert result.success
