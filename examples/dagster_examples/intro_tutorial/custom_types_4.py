import csv

from dagster import (
    DagsterType,
    EventMetadataEntry,
    Field,
    Selector,
    String,
    TypeCheck,
    execute_pipeline,
    input_hydration_config,
    pipeline,
    solid,
)


def less_simple_data_frame_type_check(_, value):
    if not isinstance(value, list):
        return TypeCheck(
            success=False,
            description=(
                'LessSimpleDataFrame should be a list of dicts, got '
                '{type_}'
            ).format(type_=type(value)),
        )

    fields = [field for field in value[0].keys()]

    for i in range(len(value)):
        row = value[i]
        if not isinstance(row, dict):
            return TypeCheck(
                success=False,
                description=(
                    'LessSimpleDataFrame should be a list of dicts, '
                    'got {type_} for row {idx}'
                ).format(type_=type(row), idx=(i + 1)),
            )
        row_fields = [field for field in row.keys()]
        if fields != row_fields:
            return TypeCheck(
                success=False,
                description=(
                    'Rows in LessSimpleDataFrame should have the same fields, '
                    'got {actual} for row {idx}, expected {expected}'
                ).format(actual=row_fields, idx=(i + 1), expected=fields),
            )

    return TypeCheck(
        success=True,
        description='LessSimpleDataFrame summary statistics',
        metadata_entries=[
            EventMetadataEntry.text(
                str(len(value)),
                'n_rows',
                'Number of rows seen in the data frame',
            ),
            EventMetadataEntry.text(
                str(len(value[0].keys()) if len(value) > 0 else 0),
                'n_cols',
                'Number of columns seen in the data frame',
            ),
            EventMetadataEntry.text(
                str(list(value[0].keys()) if len(value) > 0 else []),
                'column_names',
                'Keys of columns seen in the data frame',
            ),
        ],
    )


@input_hydration_config(Selector({'csv': Field(String)}))
def less_simple_data_frame_input_hydration_config(context, selector):
    with open(selector['csv'], 'r') as fd:
        lines = [row for row in csv.DictReader(fd)]

    context.log.info('Read {n_lines} lines'.format(n_lines=len(lines)))
    return lines


LessSimpleDataFrame = DagsterType(
    name='LessSimpleDataFrame',
    description='A more sophisticated data frame that type checks its structure.',
    type_check_fn=less_simple_data_frame_type_check,
    input_hydration_config=less_simple_data_frame_input_hydration_config,
)


@solid
def sort_by_calories(context, cereals: LessSimpleDataFrame):
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
    sort_by_calories()


if __name__ == '__main__':
    execute_pipeline(
        custom_type_pipeline,
        {
            'solids': {
                'sort_by_calories': {
                    'inputs': {'cereals': {'csv': 'cereal.csv'}}
                }
            }
        },
    )
