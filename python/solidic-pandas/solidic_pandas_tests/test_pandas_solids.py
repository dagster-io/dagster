import pandas as pd

import check

from solidic.execution import (
    materialize_input, execute_solid, SolidExecutionContext, materialize_output,
    materialize_output_in_memory, execute_pipeline, execute_single_output_pipeline
)
from solidic.types import SolidPath
from solidic.definitions import (Solid, SolidOutputTypeDefinition)
from solidic.graph import SolidRepo
import solidic_pandas as solidic_pd
from solidic_pandas.definitions import create_solidic_pandas_csv_input

from .test_utils import (script_relative_path, get_temp_file_name)


def create_test_context():
    return SolidExecutionContext()


def test_pandas_input():
    csv_input = create_solidic_pandas_csv_input(name='num_csv')
    df = materialize_input(
        create_test_context(), csv_input, {'path': script_relative_path('num.csv')}
    )

    assert isinstance(df, pd.DataFrame)
    assert df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4]}


def test_pandas_solid():
    csv_input = create_solidic_pandas_csv_input(name='num_csv')

    def transform(num_csv):
        num_csv['sum'] = num_csv['num1'] + num_csv['num2']
        return num_csv

    test_output = {}

    def output_fn_inst(df, _output_arg_dict):
        assert isinstance(df, pd.DataFrame)
        test_output['df'] = df

    custom_output_type_def = SolidOutputTypeDefinition(
        name='CUSTOM',
        output_fn=output_fn_inst,
        argument_def_dict={},
    )

    single_solid = Solid(
        name='sum_table',
        inputs=[csv_input],
        transform_fn=transform,
        output_type_defs=[custom_output_type_def],
    )

    execute_solid(
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

    def output_fn_inst(df, output_arg_dict):
        path = check.str_elem(output_arg_dict, 'path')
        df.to_csv(path, index=False)

    csv_output_type_def = SolidOutputTypeDefinition(
        name='CSV', output_fn=output_fn_inst, argument_def_dict={'path': SolidPath}
    )

    solid = Solid(
        name='sum_table',
        inputs=[csv_input],
        transform_fn=transform,
        output_type_defs=[csv_output_type_def],
    )

    output_df = execute_transform_in_temp_file(solid)

    assert output_df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def execute_transform_in_temp_file(solid):
    with get_temp_file_name() as temp_file_name:
        result = execute_solid(
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

    return solidic_pd.tabular_solid(
        name='sum_table',
        inputs=[solidic_pd.csv_input('num_csv')],
        transform_fn=transform,
    )


def create_mult_table(sum_table_solid):
    def transform(sum_table):
        sum_table['sum_squared'] = sum_table['sum'] * sum_table['sum']
        return sum_table

    return solidic_pd.tabular_solid(
        name='mult_table',
        inputs=[solidic_pd.dependency_input(sum_table_solid)],
        transform_fn=transform
    )


def test_pandas_csv_to_csv_better_api():
    solid = create_sum_table()
    output_df = execute_transform_in_temp_file(solid)
    assert output_df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def test_pandas_csv_in_memory():
    solid = create_sum_table()
    input_args = {'num_csv': {'path': script_relative_path('num.csv')}}
    df = materialize_output(create_test_context(), solid, input_args)
    assert isinstance(df, pd.DataFrame)
    assert df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def test_two_step_pipeline_in_memory():
    sum_table_solid = create_sum_table()
    mult_table_solid = create_mult_table(sum_table_solid)
    input_args = {'num_csv': {'path': script_relative_path('num.csv')}}
    context = create_test_context()
    df = materialize_output(context, sum_table_solid, input_args)
    mult_df = materialize_output_in_memory(context, mult_table_solid, {'sum_table': df})
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

    two_input_solid = solidic_pd.tabular_solid(
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

    df = materialize_output(create_test_context(), two_input_solid, input_args)
    assert isinstance(df, pd.DataFrame)
    assert df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def test_no_transform_solid():
    num_table = solidic_pd.tabular_solid(
        name='num_table',
        inputs=[solidic_pd.csv_input('num_csv')],
    )
    input_args = {'num_csv': {'path': script_relative_path('num.csv')}}
    context = create_test_context()
    df = materialize_output(context, num_table, input_args)
    assert df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4]}


def create_diamond_repo():
    return SolidRepo(solids=list(create_diamond_dag()))


def create_diamond_dag():
    num_table = solidic_pd.tabular_solid(
        name='num_table',
        inputs=[solidic_pd.csv_input('num_csv')],
    )

    def sum_transform(num_table):
        sum_table = num_table.copy()
        sum_table['sum'] = num_table['num1'] + num_table['num2']
        return sum_table

    sum_table = solidic_pd.tabular_solid(
        name='sum_table',
        inputs=[solidic_pd.dependency_input(num_table)],
        transform_fn=sum_transform,
    )

    def mult_transform(num_table):
        mult_table = num_table.copy()
        mult_table['mult'] = num_table['num1'] * num_table['num2']
        return mult_table

    mult_table = solidic_pd.tabular_solid(
        name='mult_table',
        inputs=[solidic_pd.dependency_input(num_table)],
        transform_fn=mult_transform,
    )

    def sum_mult_transform(sum_table, mult_table):
        sum_mult_table = sum_table.copy()
        sum_mult_table['mult'] = mult_table['mult']
        sum_mult_table['sum_mult'] = sum_table['sum'] * mult_table['mult']
        return sum_mult_table

    sum_mult_table = solidic_pd.tabular_solid(
        name='sum_mult_table',
        inputs=[solidic_pd.dependency_input(sum_table),
                solidic_pd.dependency_input(mult_table)],
        transform_fn=sum_mult_transform,
    )

    return (num_table, sum_table, mult_table, sum_mult_table)


def test_diamond_dag_run():
    num_table, sum_table, mult_table, sum_mult_table = create_diamond_dag()

    input_args = {'num_csv': {'path': script_relative_path('num.csv')}}
    context = create_test_context()

    num_table_df = materialize_output(context, num_table, input_args)
    assert num_table_df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4]}

    sum_df = materialize_output_in_memory(context, sum_table, {'num_table': num_table_df})

    assert sum_df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}

    mult_df = materialize_output_in_memory(context, mult_table, {'num_table': num_table_df})

    assert mult_df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'mult': [2, 12]}

    sum_mult_df = materialize_output_in_memory(
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


from collections import namedtuple

from solidic.execution import (OutputConfig, output_pipeline)


def csv_output_config(name, path):
    check.str_param(name, 'name')
    check.str_param(path, 'path')
    return OutputConfig(name=name, output_type='CSV', output_args={'path': path})


def output_solid_dag(context, repo, input_args, outputs):
    check.inst_param(context, 'context', SolidExecutionContext)
    check.inst_param(repo, 'repo', SolidRepo)
    check.dict_param(input_args, 'input_args', key_type=str, value_type=dict)
    check.list_param(outputs, 'outputs', of_type=OutputConfig)

    # iterate over materialize_solid_dags,


def materialize_solid_dag(context, repo, input_args, solid_names):
    check.inst_param(context, 'context', SolidExecutionContext)
    check.inst_param(repo, 'repo', SolidRepo)
    check.dict_param(input_args, 'input_args', key_type=str, value_type=dict)
    check.list_param(solid_names, 'solid_names', of_type=str)

    # at each node check to see if there any output configs. if so, execute them


def test_pandas_in_memory_pipeline():
    context = create_test_context()
    input_args = {'num_csv': {'path': script_relative_path('num.csv')}}

    output_df = execute_single_output_pipeline(
        context, create_diamond_repo(), input_arg_dicts=input_args, output_name='sum_mult_table'
    )

    assert output_df.to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
        'mult': [2, 12],
        'sum_mult': [6, 84],
    }


def test_pandas_output_csv_pipeline():
    context = create_test_context()
    input_args = {'num_csv': {'path': script_relative_path('num.csv')}}

    import os

    with get_temp_file_name() as temp_file_name:

        for _step in output_pipeline(
            context,
            repo=create_diamond_repo(),
            input_arg_dicts=input_args,
            output_configs=[csv_output_config('sum_mult_table', temp_file_name)]
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
