import csv
import os

from dagster import (
    EventMetadataEntry,
    Field,
    Materialization,
    Selector,
    String,
    execute_pipeline,
    input_hydration_config,
    output_materialization_config,
    pipeline,
    solid,
    usable_as_dagster_type,
)


@input_hydration_config(Selector({'csv': Field(String)}))
def less_simple_data_frame_input_hydration_config(context, selector):
    with open(selector['csv'], 'r') as fd:
        lines = [row for row in csv.DictReader(fd)]

    context.log.info('Read {n_lines} lines'.format(n_lines=len(lines)))
    return LessSimpleDataFrame(lines)


@output_materialization_config(
    Selector(
        {
            'csv': Field(
                {
                    'path': String,
                    'sep': Field(
                        String, is_required=False, default_value=','
                    ),
                },
                is_required=False,
            )
        }
    )
)
def less_simple_data_frame_output_materialization_config(
    context, config, value
):
    csv_path = os.path.abspath(config['csv']['path'])
    with open(csv_path, 'w') as fd:
        fieldnames = list(value[0].keys())
        writer = csv.DictWriter(
            fd, fieldnames, delimiter=config['csv']['sep']
        )
        writer.writeheader()
        writer.writerows(value)
    context.log.debug(
        'Wrote dataframe as .csv to {path}'.format(path=csv_path)
    )
    return Materialization(
        'data_frame_csv',
        'LessSimpleDataFrame materialized as csv',
        [EventMetadataEntry.path(csv_path, 'data_frame_csv_path')],
    )


@usable_as_dagster_type(
    name='LessSimpleDataFrame',
    description='A more sophisticated data frame that type checks its structure.',
    input_hydration_config=less_simple_data_frame_input_hydration_config,
    output_materialization_config=less_simple_data_frame_output_materialization_config,
)
class LessSimpleDataFrame(list):
    pass


@solid
def sort_by_calories(
    context, cereals: LessSimpleDataFrame
) -> LessSimpleDataFrame:
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
    return LessSimpleDataFrame(sorted_cereals)


@pipeline
def output_materialization_pipeline():
    sort_by_calories()


if __name__ == '__main__':
    execute_pipeline(
        output_materialization_pipeline,
        {
            'solids': {
                'sort_by_calories': {
                    'inputs': {'cereals': {'csv': 'cereal.csv'}},
                    'outputs': [
                        {'result': {'csv': {'path': 'cereal_out.csv'}}}
                    ],
                }
            }
        },
    )
