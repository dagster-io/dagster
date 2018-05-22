import os

import pandas as pd

from dagster import check
import solidic
from solidic.definitions import (Solid, SolidOutputDefinition)
from solidic.execution import (
    SolidExecutionContext, execute_pipeline_through_solid, _execute_input, output_pipeline_iterator,
    output_single_solid, _pipeline_solid, _pipeline_solid_in_memory, output_pipeline,
    execute_pipeline
)
import solidic_pandas as solidic_pd
from solidic_pandas.definitions import create_solidic_pandas_csv_input
from dagster.utils.test import (get_temp_file_name, get_temp_file_names, script_relative_path)


def create_test_context():
    return SolidExecutionContext()


def test_pandas_input():
    csv_input = create_solidic_pandas_csv_input(name='num_csv')
    df = _execute_input(create_test_context(), csv_input, {'path': script_relative_path('num.csv')})

    assert isinstance(df, pd.DataFrame)
    assert df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4]}


def test_pandas_solid():
    csv_input = create_solidic_pandas_csv_input(name='num_csv')

    def transform(num_csv):
        num_csv['sum'] = num_csv['num1'] + num_csv['num2']
        return num_csv

    test_output = {}

    def output_fn_inst(df, context, arg_dict):
        assert isinstance(df, pd.DataFrame)
        assert isinstance(context, SolidExecutionContext)
        assert isinstance(arg_dict, dict)

        test_output['df'] = df

    custom_output_def = SolidOutputDefinition(
        name='CUSTOM',
        output_fn=output_fn_inst,
        argument_def_dict={},
    )

    single_solid = Solid(
        name='sum_table',
        inputs=[csv_input],
        transform_fn=transform,
        outputs=[custom_output_def],
    )

    output_single_solid(
        create_test_context(),
        single_solid,
        input_arg_dicts={'num_csv': {
            'path': script_relative_path('num.csv')
        }},
        output_type='CUSTOM',
        output_arg_dict={},
    )

    assert test_output['df'].to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def test_pandas_csv_to_csv():
    csv_input = create_solidic_pandas_csv_input(name='num_csv')

    def transform(num_csv):
        num_csv['sum'] = num_csv['num1'] + num_csv['num2']
        return num_csv

    def output_fn_inst(df, context, arg_dict):
        assert isinstance(context, SolidExecutionContext)
        path = check.str_elem(arg_dict, 'path')
        df.to_csv(path, index=False)

    csv_output_def = SolidOutputDefinition(
        name='CSV', output_fn=output_fn_inst, argument_def_dict={'path': solidic.PATH}
    )

    solid = Solid(
        name='sum_table',
        inputs=[csv_input],
        transform_fn=transform,
        outputs=[csv_output_def],
    )

    output_df = execute_transform_in_temp_file(solid)

    assert output_df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def execute_transform_in_temp_file(solid):
    with get_temp_file_name() as temp_file_name:
        result = output_single_solid(
            create_test_context(),
            solid,
            input_arg_dicts={'num_csv': {
                'path': script_relative_path('num.csv')
            }},
            output_type='CSV',
            output_arg_dict={'path': temp_file_name},
        )

        assert result.success

        output_df = pd.read_csv(temp_file_name)
    return output_df


def create_sum_table():
    def transform(num_csv):
        check.inst_param(num_csv, 'num_csv', pd.DataFrame)
        num_csv['sum'] = num_csv['num1'] + num_csv['num2']
        return num_csv

    return solidic_pd.dataframe_solid(
        name='sum_table',
        inputs=[solidic_pd.csv_input('num_csv')],
        transform_fn=transform,
    )


def create_mult_table(sum_table_solid):
    def transform(sum_table):
        sum_table['sum_squared'] = sum_table['sum'] * sum_table['sum']
        return sum_table

    return solidic_pd.dataframe_solid(
        name='mult_table', inputs=[solidic_pd.depends_on(sum_table_solid)], transform_fn=transform
    )


def test_pandas_csv_to_csv_better_api():
    solid = create_sum_table()
    output_df = execute_transform_in_temp_file(solid)
    assert output_df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def test_pandas_csv_in_memory():
    solid = create_sum_table()
    input_args = {'num_csv': {'path': script_relative_path('num.csv')}}
    df = _pipeline_solid(create_test_context(), solid, input_args)
    assert isinstance(df, pd.DataFrame)
    assert df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def test_two_step_pipeline_in_memory():
    sum_table_solid = create_sum_table()
    mult_table_solid = create_mult_table(sum_table_solid)
    input_args = {'num_csv': {'path': script_relative_path('num.csv')}}
    context = create_test_context()
    df = _pipeline_solid(context, sum_table_solid, input_args)
    mult_df = _pipeline_solid_in_memory(context, mult_table_solid, {'sum_table': df})
    assert mult_df.to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
        'sum_squared': [9, 49]
    }


def test_two_input_solid():
    def transform(num_csv1, num_csv2):
        check.inst_param(num_csv1, 'num_csv1', pd.DataFrame)
        check.inst_param(num_csv2, 'num_csv2', pd.DataFrame)
        num_csv1['sum'] = num_csv1['num1'] + num_csv2['num2']
        return num_csv1

    two_input_solid = solidic_pd.dataframe_solid(
        name='two_input_solid',
        inputs=[solidic_pd.csv_input('num_csv1'),
                solidic_pd.csv_input('num_csv2')],
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

    df = _pipeline_solid(create_test_context(), two_input_solid, input_args)
    assert isinstance(df, pd.DataFrame)
    assert df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def test_no_transform_solid():
    num_table = solidic_pd.dataframe_solid(
        name='num_table',
        inputs=[solidic_pd.csv_input('num_csv')],
    )
    input_args = {'num_csv': {'path': script_relative_path('num.csv')}}
    context = create_test_context()
    df = _pipeline_solid(context, num_table, input_args)
    assert df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4]}


def create_diamond_pipeline():
    return solidic.pipeline(solids=list(create_diamond_dag()))


def create_diamond_dag():
    num_table = solidic_pd.dataframe_solid(
        name='num_table',
        inputs=[solidic_pd.csv_input('num_csv')],
    )

    def sum_transform(num_table):
        sum_table = num_table.copy()
        sum_table['sum'] = num_table['num1'] + num_table['num2']
        return sum_table

    sum_table = solidic_pd.dataframe_solid(
        name='sum_table',
        inputs=[solidic_pd.depends_on(num_table)],
        transform_fn=sum_transform,
    )

    def mult_transform(num_table):
        mult_table = num_table.copy()
        mult_table['mult'] = num_table['num1'] * num_table['num2']
        return mult_table

    mult_table = solidic_pd.dataframe_solid(
        name='mult_table',
        inputs=[solidic_pd.depends_on(num_table)],
        transform_fn=mult_transform,
    )

    def sum_mult_transform(sum_table, mult_table):
        sum_mult_table = sum_table.copy()
        sum_mult_table['mult'] = mult_table['mult']
        sum_mult_table['sum_mult'] = sum_table['sum'] * mult_table['mult']
        return sum_mult_table

    sum_mult_table = solidic_pd.dataframe_solid(
        name='sum_mult_table',
        inputs=[solidic_pd.depends_on(sum_table),
                solidic_pd.depends_on(mult_table)],
        transform_fn=sum_mult_transform,
    )

    return (num_table, sum_table, mult_table, sum_mult_table)


def test_diamond_dag_run():
    num_table, sum_table, mult_table, sum_mult_table = create_diamond_dag()

    input_args = {'num_csv': {'path': script_relative_path('num.csv')}}
    context = create_test_context()

    num_table_df = _pipeline_solid(context, num_table, input_args)
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

    result = execute_pipeline_through_solid(
        context, create_diamond_pipeline(), input_arg_dicts=input_args, solid_name='sum_mult_table'
    )

    assert result.materialized_output.to_dict('list') == {
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
        output_arg_dicts = {'sum_mult_table': {'CSV': {'path': temp_file_name}}}

        for _result in output_pipeline_iterator(
            context,
            pipeline=create_diamond_pipeline(),
            input_arg_dicts=input_arg_dicts,
            output_arg_dicts=output_arg_dicts,
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


def csv_output_arg_dict(path):
    return {'CSV': {'path': path}}


def test_pandas_output_intermediate_csv_files():
    context = create_test_context()
    input_args = {'num_csv': {'path': script_relative_path('num.csv')}}
    pipeline = create_diamond_pipeline()

    with get_temp_file_names(2) as temp_tuple:
        sum_file, mult_file = temp_tuple  # pylint: disable=E0632

        output_arg_dicts = {
            'sum_table': csv_output_arg_dict(sum_file),
            'mult_table': csv_output_arg_dict(mult_file),
        }

        subgraph_one_results = output_pipeline(
            context,
            pipeline,
            input_arg_dicts=input_args,
            output_arg_dicts=output_arg_dicts,
        )

        assert len(subgraph_one_results) == 3

        expected_sum = {
            'num1': [1, 3],
            'num2': [2, 4],
            'sum': [3, 7],
        }

        assert pd.read_csv(sum_file).to_dict('list') == expected_sum
        assert _result_named(subgraph_one_results,
                             'sum_table').materialized_output.to_dict('list') == expected_sum

        expected_mult = {
            'num1': [1, 3],
            'num2': [2, 4],
            'mult': [2, 12],
        }
        assert pd.read_csv(mult_file).to_dict('list') == expected_mult
        assert _result_named(subgraph_one_results,
                             'mult_table').materialized_output.to_dict('list') == expected_mult

        subgraph_two_results = execute_pipeline(
            context,
            pipeline,
            input_arg_dicts={
                'sum_table': {
                    'path': sum_file,
                    'format': 'CSV'
                },
                'mult_table': {
                    'path': mult_file,
                    'format': 'CSV'
                },
            },
            through_solids=['sum_mult_table'],
        )

        assert len(subgraph_two_results) == 1
        output_df = subgraph_two_results[0].materialized_output
        assert output_df.to_dict('list') == {
            'num1': [1, 3],
            'num2': [2, 4],
            'sum': [3, 7],
            'mult': [2, 12],
            'sum_mult': [6, 84],
        }


def parquet_output_arg_dict(path):
    return {'PARQUET': {'path': path}}


def test_pandas_output_intermediate_parquet_files():
    context = create_test_context()
    input_args = {'num_csv': {'path': script_relative_path('num.csv')}}
    pipeline = create_diamond_pipeline()

    with get_temp_file_names(2) as temp_tuple:
        # false positive on pylint error
        sum_file, mult_file = temp_tuple  # pylint: disable=E0632
        output_arg_dicts = {
            'sum_table': parquet_output_arg_dict(sum_file),
            'mult_table': parquet_output_arg_dict(mult_file),
        }
        output_pipeline(
            context,
            pipeline,
            input_arg_dicts=input_args,
            output_arg_dicts=output_arg_dicts,
        )

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

    def transform_fn(num_csv1, num_csv2):
        return num_csv1 + num_csv2

    double_sum = solidic_pd.dataframe_solid(
        name='double_sum',
        inputs=[solidic_pd.csv_input('num_csv1'),
                solidic_pd.csv_input('num_csv2')],
        transform_fn=transform_fn
    )

    output_df = execute_pipeline_through_solid(
        context,
        solidic.pipeline(solids=[double_sum]),
        input_arg_dicts=input_args,
        solid_name='double_sum'
    ).materialized_output

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
        output_arg_dicts = {
            'sum_mult_table': {
                'CSV': {
                    'path': csv_file
                },
                'PARQUET': {
                    'path': parquet_file
                },
            }
        }

        for _result in output_pipeline_iterator(
            context,
            pipeline=create_diamond_pipeline(),
            input_arg_dicts=input_arg_dicts,
            output_arg_dicts=output_arg_dicts,
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
