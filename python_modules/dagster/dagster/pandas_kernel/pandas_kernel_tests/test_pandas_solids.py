import os
import pytest

import pandas as pd

from dagster import (
    ArgumentDefinition,
    DependencyDefinition,
    ExecutionContext,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    SolidDefinition,
    check,
    config,
)
from dagster.core import types
from dagster.core.decorators import solid
from dagster.core.execution import (
    ExecutionContext,
    execute_pipeline_iterator,
    output_single_solid,
    execute_pipeline,
    execute_single_solid,
)
import dagster.pandas_kernel as dagster_pd
from dagster.utils.compatability import create_single_materialization_output
from dagster.utils.test import (get_temp_file_name, get_temp_file_names, script_relative_path)


def _dataframe_solid(name, inputs, transform_fn):
    return SolidDefinition.single_output_transform(
        name=name,
        inputs=inputs,
        transform_fn=transform_fn,
        output=OutputDefinition(dagster_type=dagster_pd.DataFrame),
    )


def get_solid_transformed_value(_context, solid_inst, environment):
    pipeline = PipelineDefinition(
        solids=[dagster_pd.load_csv_solid('load_csv'), solid_inst],
        dependencies={
            solid_inst.name: {
                solid_inst.inputs[0].name: DependencyDefinition('load_csv'),
            }
        }
    )

    pipeline_result = execute_pipeline(pipeline, environment)

    execution_result = pipeline_result.result_named(solid_inst.name)

    # execution_result = execute_single_solid(
    #     context,
    #     solid_inst,
    #     environment=environment,
    # )
    return execution_result.transformed_value


def get_num_csv_environment(load_csv_solid_name, materializations=None, through_solids=None):
    return config.Environment(
        solids={load_csv_solid_name: config.Solid({
            'path': script_relative_path('num.csv')
        })},
        materializations=materializations,
        execution=config.Execution(through_solids=through_solids),
    )


def create_test_context():
    return ExecutionContext()


def test_basic_pandas_solid():
    csv_input = InputDefinition('num_csv', dagster_pd.DataFrame)

    def transform(_context, args):
        num_csv = args['num_csv']
        num_csv['sum'] = num_csv['num1'] + num_csv['num2']
        return num_csv

    test_output = {}

    def materialization_fn_inst(context, arg_dict, df):
        assert isinstance(df, pd.DataFrame)
        assert isinstance(context, ExecutionContext)
        assert isinstance(arg_dict, dict)

        test_output['df'] = df

    custom_output_def = create_single_materialization_output(
        name='CUSTOM',
        materialization_fn=materialization_fn_inst,
        argument_def_dict={},
    )

    single_solid = SolidDefinition.single_output_transform(
        name='sum_table',
        inputs=[csv_input],
        transform_fn=transform,
        output=custom_output_def,
    )

    pipeline = PipelineDefinition(
        solids=[dagster_pd.load_csv_solid('load_csv'), single_solid],
        dependencies={single_solid.name: {
            'num_csv': DependencyDefinition('load_csv'),
        }}
    )

    execute_pipeline(
        pipeline,
        environment=get_num_csv_environment(
            'load_csv',
            materializations=[config.Materialization(solid='sum_table', name='CUSTOM', args={})]
        ),
    )

    assert test_output['df'].to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def test_pandas_csv_to_csv():
    csv_input = InputDefinition('num_csv', dagster_pd.DataFrame)

    # just adding a second context arg to test that
    def transform(context, args):
        check.inst_param(context, 'context', ExecutionContext)
        num_csv = args['num_csv']
        num_csv['sum'] = num_csv['num1'] + num_csv['num2']
        return num_csv

    def materialization_fn_inst(context, arg_dict, df):
        assert isinstance(context, ExecutionContext)
        path = check.str_elem(arg_dict, 'path')
        df.to_csv(path, index=False)

    csv_output_def = create_single_materialization_output(
        name='CSV',
        materialization_fn=materialization_fn_inst,
        argument_def_dict={'path': ArgumentDefinition(types.Path)}
    )

    solid_def = SolidDefinition.single_output_transform(
        name='sum_table',
        inputs=[csv_input],
        transform_fn=transform,
        output=csv_output_def,
    )

    output_df = execute_transform_in_temp_csv_files(solid_def)

    assert output_df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def execute_transform_in_temp_csv_files(solid_inst):
    load_csv_solid = dagster_pd.load_csv_solid('load_csv')
    pipeline = PipelineDefinition(
        solids=[load_csv_solid, solid_inst],
        dependencies={
            solid_inst.name: {
                solid_inst.inputs[0].name: DependencyDefinition('load_csv'),
            }
        }
    )
    with get_temp_file_name() as temp_file_name:
        result = execute_pipeline(
            pipeline,
            get_num_csv_environment(
                'load_csv',
                materializations=[
                    config.Materialization(
                        solid=solid_inst.name,
                        name='CSV',
                        args={'path': temp_file_name},
                    )
                ]
            ),
        )

        assert result.success

        output_df = pd.read_csv(temp_file_name)

    return output_df


def create_sum_table():
    def transform(_context, args):
        num_csv = args['num_csv']
        check.inst_param(num_csv, 'num_csv', pd.DataFrame)
        num_csv['sum'] = num_csv['num1'] + num_csv['num2']
        return num_csv

    return _dataframe_solid(
        name='sum_table',
        inputs=[InputDefinition('num_csv', dagster_pd.DataFrame)],
        transform_fn=transform,
    )


@solid(
    inputs=[InputDefinition('num_csv', dagster_pd.DataFrame)],
    output=OutputDefinition(dagster_type=dagster_pd.DataFrame),
)
def sum_table(num_csv):
    check.inst_param(num_csv, 'num_csv', pd.DataFrame)
    num_csv['sum'] = num_csv['num1'] + num_csv['num2']
    return num_csv


@solid(
    inputs=[InputDefinition('sum_df', dagster_pd.DataFrame)],
    output=OutputDefinition(dagster_type=dagster_pd.DataFrame),
)
def sum_sq_table(sum_df):
    sum_df['sum_squared'] = sum_df['sum'] * sum_df['sum']
    return sum_df


@solid(
    inputs=[InputDefinition('sum_table_renamed', dagster_pd.DataFrame)],
    output=OutputDefinition(dagster_type=dagster_pd.DataFrame),
)
def sum_sq_table_renamed_input(sum_table_renamed):
    sum_table_renamed['sum_squared'] = sum_table_renamed['sum'] * sum_table_renamed['sum']
    return sum_table_renamed


def create_mult_table(sum_table_solid):
    def transform(_context, args):
        sum_df = args['sum_table']
        sum_df['sum_squared'] = sum_df['sum'] * sum_df['sum']
        return sum_df

    return _dataframe_solid(
        name='mult_table',
        inputs=[InputDefinition('sum_table', dagster_pd.DataFrame)],
        transform_fn=transform
    )


def test_pandas_csv_to_csv_better_api():
    output_df = execute_transform_in_temp_csv_files(create_sum_table())
    assert output_df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def test_pandas_csv_to_csv_decorator_api():
    output_df = execute_transform_in_temp_csv_files(sum_table)
    assert output_df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def test_pandas_csv_in_memory():
    df = get_solid_transformed_value(
        None,
        create_sum_table(),
        get_num_csv_environment('load_csv'),
    )
    assert isinstance(df, pd.DataFrame)
    assert df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def _sum_only_pipeline():
    return PipelineDefinition(
        solids=[sum_table, sum_sq_table],
        dependencies={},
    )


def test_two_input_solid():
    def transform(_context, args):
        num_csv1 = args['num_csv1']
        num_csv2 = args['num_csv2']
        check.inst_param(num_csv1, 'num_csv1', pd.DataFrame)
        check.inst_param(num_csv2, 'num_csv2', pd.DataFrame)
        num_csv1['sum'] = num_csv1['num1'] + num_csv2['num2']
        return num_csv1

    two_input_solid = _dataframe_solid(
        name='two_input_solid',
        inputs=[
            InputDefinition('num_csv1', dagster_pd.DataFrame),
            InputDefinition('num_csv2', dagster_pd.DataFrame),
        ],
        transform_fn=transform,
    )

    environment = config.Environment(
        solids={
            'load_csv1': config.Solid({
                'path': script_relative_path('num.csv')
            }),
            'load_csv2': config.Solid({
                'path': script_relative_path('num.csv')
            }),
        }
    )

    pipeline = PipelineDefinition(
        solids=[
            dagster_pd.load_csv_solid('load_csv1'),
            dagster_pd.load_csv_solid('load_csv2'), two_input_solid
        ],
        dependencies={
            'two_input_solid': {
                'num_csv1': DependencyDefinition('load_csv1'),
                'num_csv2': DependencyDefinition('load_csv2'),
            }
        }
    )

    pipeline_result = execute_pipeline(pipeline, environment)
    assert pipeline_result.success

    df = pipeline_result.result_named('two_input_solid').transformed_value

    # df = get_solid_transformed_value(create_test_context(), two_input_solid, environment)
    assert isinstance(df, pd.DataFrame)
    assert df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def test_no_transform_solid():
    num_table = _dataframe_solid(
        name='num_table',
        inputs=[InputDefinition('num_csv', dagster_pd.DataFrame)],
        transform_fn=lambda _context, args: args['num_csv'],
    )
    context = create_test_context()
    df = get_solid_transformed_value(context, num_table, get_num_csv_environment('load_csv'))
    assert df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4]}


def create_diamond_pipeline():
    return PipelineDefinition(solids=list(create_diamond_dag()), dependencies=create_diamond_deps())


def create_diamond_deps():
    return {
        'num_table': {
            'num_csv': DependencyDefinition('load_csv'),
        },
        'sum_table': {
            'num_table': DependencyDefinition('num_table'),
        },
        'mult_table': {
            'num_table': DependencyDefinition('num_table'),
        },
        'sum_mult_table': {
            'sum_table': DependencyDefinition('sum_table'),
            'mult_table': DependencyDefinition('mult_table'),
        }
    }


def create_diamond_dag():
    load_csv_solid = dagster_pd.load_csv_solid('load_csv')

    num_table_solid = _dataframe_solid(
        name='num_table',
        inputs=[InputDefinition('num_csv', dagster_pd.DataFrame)],
        transform_fn=lambda _context, args: args['num_csv'],
    )

    def sum_transform(_context, args):
        num_df = args['num_table']
        sum_df = num_df.copy()
        sum_df['sum'] = num_df['num1'] + num_df['num2']
        return sum_df

    sum_table_solid = _dataframe_solid(
        name='sum_table',
        inputs=[InputDefinition('num_table', dagster_pd.DataFrame)],
        transform_fn=sum_transform,
    )

    def mult_transform(_context, args):
        num_table = args['num_table']
        mult_table = num_table.copy()
        mult_table['mult'] = num_table['num1'] * num_table['num2']
        return mult_table

    mult_table_solid = _dataframe_solid(
        name='mult_table',
        inputs=[InputDefinition('num_table', dagster_pd.DataFrame)],
        transform_fn=mult_transform,
    )

    def sum_mult_transform(_context, args):
        sum_df = args['sum_table']
        mult_df = args['mult_table']
        sum_mult_table = sum_df.copy()
        sum_mult_table['mult'] = mult_df['mult']
        sum_mult_table['sum_mult'] = sum_df['sum'] * mult_df['mult']
        return sum_mult_table

    sum_mult_table_solid = _dataframe_solid(
        name='sum_mult_table',
        inputs=[
            InputDefinition('sum_table', dagster_pd.DataFrame),
            InputDefinition('mult_table', dagster_pd.DataFrame),
        ],
        transform_fn=sum_mult_transform,
    )

    return (
        load_csv_solid, num_table_solid, sum_table_solid, mult_table_solid, sum_mult_table_solid
    )


def test_pandas_in_memory_diamond_pipeline():
    pipeline = create_diamond_pipeline()
    result = execute_pipeline(
        pipeline,
        environment=get_num_csv_environment('load_csv', through_solids=['sum_mult_table'])
    )

    assert result.result_named('sum_mult_table').transformed_value.to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
        'mult': [2, 12],
        'sum_mult': [6, 84],
    }


def test_pandas_output_csv_pipeline():
    with get_temp_file_name() as temp_file_name:
        pipeline = create_diamond_pipeline()
        environment = get_num_csv_environment(
            'load_csv', [
                config.Materialization(
                    solid='sum_mult_table',
                    name='CSV',
                    args={'path': temp_file_name},
                )
            ]
        )

        for _result in execute_pipeline_iterator(pipeline=pipeline, environment=environment):
            pass

        assert os.path.exists(temp_file_name)
        output_df = pd.read_csv(temp_file_name)
        assert output_df.to_dict('list') == {
            'num1': [1, 3],
            'num2': [2, 4],
            'sum': [3, 7],
            'mult': [2, 12],
            'sum_mult': [6, 84],
        }


def _result_named(results, name):
    for result in results:
        if result.name == name:
            return result

    check.failed('could not find name')


def test_pandas_output_intermediate_csv_files():
    pipeline = create_diamond_pipeline()

    with get_temp_file_names(2) as temp_tuple:
        sum_file, mult_file = temp_tuple  # pylint: disable=E0632

        environment = get_num_csv_environment(
            'load_csv', [
                config.Materialization(
                    solid='sum_table',
                    name='CSV',
                    args={'path': sum_file},
                ),
                config.Materialization(
                    solid='mult_table',
                    name='CSV',
                    args={'path': mult_file},
                ),
            ]
        )

        subgraph_one_result = execute_pipeline(pipeline, environment=environment)

        assert len(subgraph_one_result.result_list) == 5

        expected_sum = {
            'num1': [1, 3],
            'num2': [2, 4],
            'sum': [3, 7],
        }

        assert pd.read_csv(sum_file).to_dict('list') == expected_sum
        sum_table_result = subgraph_one_result.result_named('sum_table')
        assert sum_table_result.transformed_value.to_dict('list') == expected_sum

        expected_mult = {
            'num1': [1, 3],
            'num2': [2, 4],
            'mult': [2, 12],
        }
        assert pd.read_csv(mult_file).to_dict('list') == expected_mult
        mult_table_result = subgraph_one_result.result_named('mult_table')
        assert mult_table_result.transformed_value.to_dict('list') == expected_mult

        # TODO need better partial execution API
        return

        # pipeline_result = execute_pipeline(
        #     pipeline,
        #     environment=config.Environment(
        #         sources={
        #             'sum_mult_table': {
        #                 'sum_table': config.Source('CSV', {'path': sum_file}),
        #                 'mult_table': config.Source('CSV', {'path': mult_file}),
        #             },
        #         },
        #         execution=config.Execution.single_solid('sum_mult_table'),
        #     ),
        # )

        # assert pipeline_result.success

        # subgraph_two_result_list = pipeline_result.result_list

        # assert len(subgraph_two_result_list) == 1
        # output_df = subgraph_two_result_list[0].transformed_value
        # assert output_df.to_dict('list') == {
        #     'num1': [1, 3],
        #     'num2': [2, 4],
        #     'sum': [3, 7],
        #     'mult': [2, 12],
        #     'sum_mult': [6, 84],
        # }


def csv_materialization(solid_name, path):
    return config.Materialization(
        solid=solid_name,
        name='CSV',
        args={'path': path},
    )


def parquet_materialization(solid_name, path):
    return config.Materialization(
        solid=solid_name,
        name='PARQUET',
        args={'path': path},
    )


def test_pandas_output_intermediate_parquet_files():
    pipeline = create_diamond_pipeline()

    with get_temp_file_names(2) as temp_tuple:
        # false positive on pylint error
        sum_file, mult_file = temp_tuple  # pylint: disable=E0632
        pipeline_result = execute_pipeline(
            pipeline,
            environment=get_num_csv_environment(
                'load_csv', [
                    parquet_materialization('sum_table', sum_file),
                    parquet_materialization('mult_table', mult_file),
                ]
            ),
        )

        assert pipeline_result.success

        expected_sum = {
            'num1': [1, 3],
            'num2': [2, 4],
            'sum': [3, 7],
        }

        assert pd.read_parquet(sum_file).to_dict('list') == expected_sum


def test_pandas_multiple_inputs():
    environment = config.Environment(
        solids={
            'load_one': config.Solid({
                'path': script_relative_path('num.csv')
            }),
            'load_two': config.Solid({
                'path': script_relative_path('num.csv')
            }),
        },
        execution=config.Execution(through_solids=['double_sum']),
    )

    def transform_fn(_context, args):
        return args['num_csv1'] + args['num_csv2']

    double_sum = _dataframe_solid(
        name='double_sum',
        inputs=[
            InputDefinition('num_csv1', dagster_pd.DataFrame),
            InputDefinition('num_csv2', dagster_pd.DataFrame),
        ],
        transform_fn=transform_fn
    )

    pipeline = PipelineDefinition(
        solids=[
            dagster_pd.load_csv_solid('load_one'),
            dagster_pd.load_csv_solid('load_two'), double_sum
        ],
        dependencies={
            'double_sum': {
                'num_csv1': DependencyDefinition('load_one'),
                'num_csv2': DependencyDefinition('load_two'),
            }
        },
    )

    output_df = execute_pipeline(
        pipeline,
        environment=environment,
    ).result_named('double_sum').transformed_value

    assert not output_df.empty

    assert output_df.to_dict('list') == {
        'num1': [2, 6],
        'num2': [4, 8],
    }


def test_pandas_multiple_outputs():
    with get_temp_file_names(2) as temp_tuple:
        # false positive on pylint error
        csv_file, parquet_file = temp_tuple  # pylint: disable=E0632
        pipeline = create_diamond_pipeline()

        for _result in execute_pipeline_iterator(
            pipeline=pipeline,
            environment=get_num_csv_environment(
                'load_csv', [
                    csv_materialization('sum_mult_table', csv_file),
                    parquet_materialization('sum_mult_table', parquet_file),
                ]
            ),
        ):
            pass

        assert os.path.exists(csv_file)
        output_csv_df = pd.read_csv(csv_file)
        assert output_csv_df.to_dict('list') == {
            'num1': [1, 3],
            'num2': [2, 4],
            'sum': [3, 7],
            'mult': [2, 12],
            'sum_mult': [6, 84],
        }

        assert os.path.exists(parquet_file)
        output_parquet_df = pd.read_parquet(parquet_file)
        assert output_parquet_df.to_dict('list') == {
            'num1': [1, 3],
            'num2': [2, 4],
            'sum': [3, 7],
            'mult': [2, 12],
            'sum_mult': [6, 84],
        }


def test_rename_input():
    result = execute_pipeline(
        PipelineDefinition(
            solids=[dagster_pd.load_csv_solid('load_csv'), sum_table, sum_sq_table_renamed_input],
            dependencies={
                'sum_table': {
                    'num_csv': DependencyDefinition('load_csv'),
                },
                sum_sq_table_renamed_input.name: {
                    'sum_table_renamed': DependencyDefinition(sum_table.name),
                },
            },
        ),
        environment=get_num_csv_environment('load_csv'),
    )

    assert result.success

    assert result.result_named('sum_sq_table_renamed_input').transformed_value.to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
        'sum_squared': [9, 49],
    }
