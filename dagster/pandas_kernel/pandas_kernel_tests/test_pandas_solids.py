import os
import pytest

import pandas as pd

from dagster import check
from dagster import config
import dagster.core
from dagster.core import types
from dagster.core.definitions import (SolidDefinition, create_single_materialization_output)
from dagster.core.execution import (
    DagsterExecutionContext, execute_pipeline_through_solid, _read_source,
    materialize_pipeline_iterator, output_single_solid, _pipeline_solid_in_memory,
    materialize_pipeline, execute_pipeline, execute_single_solid,
    create_single_solid_env_from_arg_dicts, create_pipeline_env_from_arg_dicts
)
import dagster.pandas_kernel as dagster_pd
from dagster.utils.test import (get_temp_file_name, get_temp_file_names, script_relative_path)
from .utils import simple_csv_input


def get_solid_tranformed_value(context, solid, input_arg_dicts):
    execution_result = execute_single_solid(
        context, solid, environment=create_single_solid_env_from_arg_dicts(solid, input_arg_dicts)
    )
    return execution_result.transformed_value


def create_test_context():
    return DagsterExecutionContext()


def test_pandas_input():
    csv_input = simple_csv_input('num_csv')
    df = _read_source(
        create_test_context(), csv_input.sources[0], {'path': script_relative_path('num.csv')}
    )

    assert isinstance(df, pd.DataFrame)
    assert df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4]}


def test_pandas_solid():
    csv_input = simple_csv_input('num_csv')

    def transform(context, args):
        num_csv = args['num_csv']
        num_csv['sum'] = num_csv['num1'] + num_csv['num2']
        return num_csv

    test_output = {}

    def materialization_fn_inst(context, arg_dict, df):
        assert isinstance(df, pd.DataFrame)
        assert isinstance(context, DagsterExecutionContext)
        assert isinstance(arg_dict, dict)

        test_output['df'] = df

    custom_output_def = create_single_materialization_output(
        materialization_type='CUSTOM',
        materialization_fn=materialization_fn_inst,
        argument_def_dict={},
    )

    single_solid = SolidDefinition(
        name='sum_table',
        inputs=[csv_input],
        transform_fn=transform,
        output=custom_output_def,
    )

    output_single_solid(
        create_test_context(),
        single_solid,
        environment=create_single_solid_env_from_arg_dicts(
            single_solid, {'num_csv': {
                'path': script_relative_path('num.csv')
            }}
        ),
        materialization_type='CUSTOM',
        arg_dict={},
    )

    assert test_output['df'].to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def test_pandas_csv_to_csv():
    csv_input = simple_csv_input('num_csv')

    # just adding a second context arg to test that
    def transform(context, args):
        check.inst_param(context, 'context', dagster.core.execution.DagsterExecutionContext)
        num_csv = args['num_csv']
        num_csv['sum'] = num_csv['num1'] + num_csv['num2']
        return num_csv

    def materialization_fn_inst(context, arg_dict, df):
        assert isinstance(context, DagsterExecutionContext)
        path = check.str_elem(arg_dict, 'path')
        df.to_csv(path, index=False)

    csv_output_def = create_single_materialization_output(
        materialization_type='CSV',
        materialization_fn=materialization_fn_inst,
        argument_def_dict={'path': types.PATH}
    )

    solid = SolidDefinition(
        name='sum_table',
        inputs=[csv_input],
        transform_fn=transform,
        output=csv_output_def,
    )

    output_df = execute_transform_in_temp_file(solid)

    assert output_df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def execute_transform_in_temp_file(solid):
    with get_temp_file_name() as temp_file_name:
        result = output_single_solid(
            create_test_context(),
            solid,
            environment=create_single_solid_env_from_arg_dicts(
                solid, {'num_csv': {
                    'path': script_relative_path('num.csv')
                }}
            ),
            materialization_type='CSV',
            arg_dict={'path': temp_file_name},
        )

        assert result.success

        output_df = pd.read_csv(temp_file_name)
    return output_df


def create_sum_table():
    def transform(context, args):
        num_csv = args['num_csv']
        check.inst_param(num_csv, 'num_csv', pd.DataFrame)
        num_csv['sum'] = num_csv['num1'] + num_csv['num2']
        return num_csv

    return dagster_pd.dataframe_solid(
        name='sum_table',
        inputs=[simple_csv_input('num_csv')],
        transform_fn=transform,
    )


def create_mult_table(sum_table_solid):
    def transform(context, args):
        sum_table = args['sum_table']
        sum_table['sum_squared'] = sum_table['sum'] * sum_table['sum']
        return sum_table

    return dagster_pd.dataframe_solid(
        name='mult_table',
        inputs=[dagster_pd.dataframe_dependency(sum_table_solid)],
        transform_fn=transform
    )


def test_pandas_csv_to_csv_better_api():
    solid = create_sum_table()
    output_df = execute_transform_in_temp_file(solid)
    assert output_df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def test_pandas_csv_in_memory():
    solid = create_sum_table()
    input_args = {'num_csv': {'path': script_relative_path('num.csv')}}
    df = get_solid_tranformed_value(create_test_context(), solid, input_args)
    assert isinstance(df, pd.DataFrame)
    assert df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def test_two_step_pipeline_in_memory():
    sum_table_solid = create_sum_table()
    mult_table_solid = create_mult_table(sum_table_solid)
    input_args = {'num_csv': {'path': script_relative_path('num.csv')}}
    context = create_test_context()
    df = get_solid_tranformed_value(context, sum_table_solid, input_args)
    mult_df = _pipeline_solid_in_memory(context, mult_table_solid, {'sum_table': df})
    assert mult_df.to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
        'sum_squared': [9, 49]
    }


def test_two_input_solid():
    def transform(contextx, args):
        num_csv1 = args['num_csv1']
        num_csv2 = args['num_csv2']
        check.inst_param(num_csv1, 'num_csv1', pd.DataFrame)
        check.inst_param(num_csv2, 'num_csv2', pd.DataFrame)
        num_csv1['sum'] = num_csv1['num1'] + num_csv2['num2']
        return num_csv1

    two_input_solid = dagster_pd.dataframe_solid(
        name='two_input_solid',
        inputs=[simple_csv_input('num_csv1'),
                simple_csv_input('num_csv2')],
        transform_fn=transform,
    )

    input_args = {
        'num_csv1': {
            'path': script_relative_path('num.csv')
        },
        'num_csv2': {
            'path': script_relative_path('num.csv')
        },
    }

    df = get_solid_tranformed_value(create_test_context(), two_input_solid, input_args)
    assert isinstance(df, pd.DataFrame)
    assert df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def test_no_transform_solid():
    num_table = dagster_pd.dataframe_solid(
        name='num_table',
        inputs=[simple_csv_input('num_csv')],
    )
    input_args = {'num_csv': {'path': script_relative_path('num.csv')}}
    context = create_test_context()
    df = get_solid_tranformed_value(context, num_table, input_args)
    assert df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4]}


def create_diamond_pipeline():
    return dagster.core.pipeline(solids=list(create_diamond_dag()))


def create_diamond_dag():
    num_table = dagster_pd.dataframe_solid(
        name='num_table',
        inputs=[simple_csv_input('num_csv')],
    )

    def sum_transform(context, args):
        num_table = args['num_table']
        sum_table = num_table.copy()
        sum_table['sum'] = num_table['num1'] + num_table['num2']
        return sum_table

    sum_table = dagster_pd.dataframe_solid(
        name='sum_table',
        inputs=[dagster_pd.dataframe_dependency(num_table)],
        transform_fn=sum_transform,
    )

    def mult_transform(context, args):
        num_table = args['num_table']
        mult_table = num_table.copy()
        mult_table['mult'] = num_table['num1'] * num_table['num2']
        return mult_table

    mult_table = dagster_pd.dataframe_solid(
        name='mult_table',
        inputs=[dagster_pd.dataframe_dependency(num_table)],
        transform_fn=mult_transform,
    )

    def sum_mult_transform(context, args):
        sum_table = args['sum_table']
        mult_table = args['mult_table']
        sum_mult_table = sum_table.copy()
        sum_mult_table['mult'] = mult_table['mult']
        sum_mult_table['sum_mult'] = sum_table['sum'] * mult_table['mult']
        return sum_mult_table

    sum_mult_table = dagster_pd.dataframe_solid(
        name='sum_mult_table',
        inputs=[
            dagster_pd.dataframe_dependency(sum_table),
            dagster_pd.dataframe_dependency(mult_table)
        ],
        transform_fn=sum_mult_transform,
    )

    return (num_table, sum_table, mult_table, sum_mult_table)


def test_diamond_dag_run():
    num_table, sum_table, mult_table, sum_mult_table = create_diamond_dag()

    input_args = {'num_csv': {'path': script_relative_path('num.csv')}}
    context = create_test_context()

    num_table_df = get_solid_tranformed_value(context, num_table, input_args)
    assert num_table_df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4]}

    sum_df = _pipeline_solid_in_memory(context, sum_table, {'num_table': num_table_df})

    assert sum_df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}

    mult_df = _pipeline_solid_in_memory(context, mult_table, {'num_table': num_table_df})

    assert mult_df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'mult': [2, 12]}

    sum_mult_df = _pipeline_solid_in_memory(
        context, sum_mult_table, {
            'sum_table': sum_df,
            'mult_table': mult_df
        }
    )

    assert sum_mult_df.to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
        'mult': [2, 12],
        'sum_mult': [6, 84],
    }


def test_pandas_in_memory_diamond_pipeline():
    context = create_test_context()
    input_args = {'num_csv': {'path': script_relative_path('num.csv')}}

    pipeline = create_diamond_pipeline()
    result = execute_pipeline_through_solid(
        context,
        pipeline,
        environment=create_pipeline_env_from_arg_dicts(pipeline, input_args),
        solid_name='sum_mult_table'
    )

    assert result.transformed_value.to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
        'mult': [2, 12],
        'sum_mult': [6, 84],
    }


def test_pandas_output_csv_pipeline():
    context = create_test_context()
    input_arg_dicts = {'num_csv': {'path': script_relative_path('num.csv')}}

    with get_temp_file_name() as temp_file_name:
        pipeline = create_diamond_pipeline()
        environment = create_pipeline_env_from_arg_dicts(pipeline, input_arg_dicts)

        for _result in materialize_pipeline_iterator(
            context,
            pipeline=pipeline,
            environment=environment,
            materializations=[
                config.Materialization(
                    solid='sum_mult_table',
                    materialization_type='CSV',
                    args={'path': temp_file_name},
                )
            ],
        ):
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
    context = create_test_context()
    input_args = {'num_csv': {'path': script_relative_path('num.csv')}}
    pipeline = create_diamond_pipeline()

    with get_temp_file_names(2) as temp_tuple:
        sum_file, mult_file = temp_tuple  # pylint: disable=E0632

        environment = create_pipeline_env_from_arg_dicts(pipeline, input_args)

        subgraph_one_result = materialize_pipeline(
            context,
            pipeline,
            environment=environment,
            materializations=[
                config.Materialization(
                    solid='sum_table',
                    materialization_type='CSV',
                    args={'path': sum_file},
                ),
                config.Materialization(
                    solid='mult_table',
                    materialization_type='CSV',
                    args={'path': mult_file},
                ),
            ],
        )

        assert len(subgraph_one_result.result_list) == 3

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

        pipeline_result = execute_pipeline(
            context,
            pipeline,
            environment=config.Environment(
                input_sources=[
                    config.Input(
                        input_name='sum_table',
                        source='CSV',
                        args={
                            'path': sum_file,
                        },
                    ),
                    config.Input(
                        input_name='mult_table',
                        source='CSV',
                        args={
                            'path': mult_file,
                        },
                    ),
                ],
            ),
            from_solids=['sum_mult_table'],
            through_solids=['sum_mult_table'],
        )

        assert pipeline_result.success

        subgraph_two_result_list = pipeline_result.result_list

        assert len(subgraph_two_result_list) == 1
        output_df = subgraph_two_result_list[0].transformed_value
        assert output_df.to_dict('list') == {
            'num1': [1, 3],
            'num2': [2, 4],
            'sum': [3, 7],
            'mult': [2, 12],
            'sum_mult': [6, 84],
        }


def csv_materialization(solid_name, path):
    return config.Materialization(
        solid=solid_name,
        materialization_type='CSV',
        args={'path': path},
    )


def parquet_materialization(solid_name, path):
    return config.Materialization(
        solid=solid_name,
        materialization_type='PARQUET',
        args={'path': path},
    )


def test_pandas_output_intermediate_parquet_files():
    context = create_test_context()
    input_args = {'num_csv': {'path': script_relative_path('num.csv')}}
    pipeline = create_diamond_pipeline()

    with get_temp_file_names(2) as temp_tuple:
        # false positive on pylint error
        sum_file, mult_file = temp_tuple  # pylint: disable=E0632
        pipeline_result = materialize_pipeline(
            context,
            pipeline,
            environment=create_pipeline_env_from_arg_dicts(pipeline, input_args),
            materializations=[
                parquet_materialization('sum_table', sum_file),
                parquet_materialization('mult_table', mult_file),
            ],
        )

        assert pipeline_result.success

        expected_sum = {
            'num1': [1, 3],
            'num2': [2, 4],
            'sum': [3, 7],
        }

        assert pd.read_parquet(sum_file).to_dict('list') == expected_sum


def test_pandas_multiple_inputs():

    context = create_test_context()

    input_args = {
        'num_csv1': {
            'path': script_relative_path('num.csv')
        },
        'num_csv2': {
            'path': script_relative_path('num.csv')
        },
    }

    def transform_fn(context, args):
        return args['num_csv1'] + args['num_csv2']

    double_sum = dagster_pd.dataframe_solid(
        name='double_sum',
        inputs=[simple_csv_input('num_csv1'),
                simple_csv_input('num_csv2')],
        transform_fn=transform_fn
    )
    pipeline = dagster.core.pipeline(solids=[double_sum])

    output_df = execute_pipeline_through_solid(
        context,
        pipeline,
        environment=create_pipeline_env_from_arg_dicts(pipeline, input_args),
        solid_name='double_sum'
    ).transformed_value

    assert not output_df.empty

    assert output_df.to_dict('list') == {
        'num1': [2, 6],
        'num2': [4, 8],
    }


def test_pandas_multiple_outputs():
    context = create_test_context()
    input_arg_dicts = {'num_csv': {'path': script_relative_path('num.csv')}}

    with get_temp_file_names(2) as temp_tuple:
        # false positive on pylint error
        csv_file, parquet_file = temp_tuple  # pylint: disable=E0632
        pipeline = create_diamond_pipeline()

        for _result in materialize_pipeline_iterator(
            context,
            pipeline=pipeline,
            environment=create_pipeline_env_from_arg_dicts(pipeline, input_arg_dicts),
            materializations=[
                csv_materialization('sum_mult_table', csv_file),
                parquet_materialization('sum_mult_table', parquet_file),
            ],
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
