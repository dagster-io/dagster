import os

import pandas as pd

from dagster import (
    ExecutionContext,
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    SolidDefinition,
    check,
    config,
    lambda_solid,
)

from dagster.core.execution import (
    execute_pipeline_iterator,
    execute_pipeline,
)

import dagster.pandas as dagster_pd

from dagster.core.test_utils import single_output_transform

from dagster.utils import script_relative_path

from dagster.utils.test import (
    get_temp_file_name,
    get_temp_file_names,
)


def _dataframe_solid(name, inputs, transform_fn):
    return single_output_transform(
        name=name,
        inputs=inputs,
        transform_fn=transform_fn,
        output=OutputDefinition(dagster_pd.DataFrame),
    )


def get_solid_transformed_value(_context, solid_inst, environment):
    pipeline = PipelineDefinition(
        solids=[dagster_pd.load_csv_solid('load_csv'), solid_inst],
        dependencies={
            solid_inst.name: {
                solid_inst.input_defs[0].name: DependencyDefinition('load_csv'),
            }
        }
    )

    pipeline_result = execute_pipeline(pipeline, environment)

    execution_result = pipeline_result.result_for_solid(solid_inst.name)

    return execution_result.transformed_value()


def get_load_only_solids_config(load_csv_solid_name):
    return {load_csv_solid_name: config.Solid({'path': script_relative_path('num.csv')})}


def get_num_csv_environment(solids_config):
    return config.Environment(solids=solids_config)


def create_test_context():
    return ExecutionContext()


def test_basic_pandas_solid():
    csv_input = InputDefinition('num_csv', dagster_pd.DataFrame)

    def transform(_context, inputs):
        num_csv = inputs['num_csv']
        num_csv['sum'] = num_csv['num1'] + num_csv['num2']
        return num_csv

    single_solid = single_output_transform(
        name='sum_table',
        inputs=[csv_input],
        transform_fn=transform,
        output=OutputDefinition(),
    )

    pipeline = PipelineDefinition(
        solids=[dagster_pd.load_csv_solid('load_csv'), single_solid],
        dependencies={single_solid.name: {
            'num_csv': DependencyDefinition('load_csv'),
        }}
    )

    pipeline_result = execute_pipeline(
        pipeline,
        environment=get_num_csv_environment(get_load_only_solids_config('load_csv')),
    )

    assert pipeline_result.success

    assert pipeline_result.result_for_solid('sum_table').transformed_value().to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7]
    }


def test_pandas_csv_to_csv():
    csv_input = InputDefinition('num_csv', dagster_pd.DataFrame)

    # just adding a second context arg to test that
    def transform(context, inputs):
        check.inst_param(context, 'context', ExecutionContext)
        num_csv = inputs['num_csv']
        num_csv['sum'] = num_csv['num1'] + num_csv['num2']
        return num_csv

    solid_def = single_output_transform(
        name='sum_table',
        inputs=[csv_input],
        transform_fn=transform,
        output=OutputDefinition(dagster_pd.DataFrame),
    )

    output_df = execute_transform_in_temp_csv_files(solid_def)

    assert output_df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def execute_transform_in_temp_csv_files(solid_inst):
    load_csv_solid = dagster_pd.load_csv_solid('load_csv')
    to_csv_solid = dagster_pd.to_csv_solid('to_csv')

    key = solid_inst.input_defs[0].name

    pipeline = PipelineDefinition(
        solids=[load_csv_solid, solid_inst, to_csv_solid],
        dependencies={
            solid_inst.name: {
                key: DependencyDefinition('load_csv'),
            },
            'to_csv': {
                'df': DependencyDefinition(solid_inst.name),
            }
        }
    )
    with get_temp_file_name() as temp_file_name:
        result = execute_pipeline(
            pipeline,
            get_num_csv_environment(
                {
                    load_csv_solid.name: config.Solid({
                        'path': script_relative_path('num.csv')
                    }),
                    to_csv_solid.name: config.Solid({
                        'path': temp_file_name
                    }),
                }
            ),
        )

        assert result.success

        output_df = pd.read_csv(temp_file_name)

    return output_df


def create_sum_table():
    def transform(_context, inputs):
        num_csv = inputs['num_csv']
        check.inst_param(num_csv, 'num_csv', pd.DataFrame)
        num_csv['sum'] = num_csv['num1'] + num_csv['num2']
        return num_csv

    return _dataframe_solid(
        name='sum_table',
        inputs=[InputDefinition('num_csv', dagster_pd.DataFrame)],
        transform_fn=transform,
    )


@lambda_solid(
    inputs=[InputDefinition('num_csv', dagster_pd.DataFrame)],
    output=OutputDefinition(dagster_pd.DataFrame),
)
def sum_table(num_csv):
    check.inst_param(num_csv, 'num_csv', pd.DataFrame)
    num_csv['sum'] = num_csv['num1'] + num_csv['num2']
    return num_csv


@lambda_solid(
    inputs=[InputDefinition('sum_df', dagster_pd.DataFrame)],
    output=OutputDefinition(dagster_pd.DataFrame),
)
def sum_sq_table(sum_df):
    sum_df['sum_squared'] = sum_df['sum'] * sum_df['sum']
    return sum_df


@lambda_solid(
    inputs=[InputDefinition('sum_table_renamed', dagster_pd.DataFrame)],
    output=OutputDefinition(dagster_pd.DataFrame),
)
def sum_sq_table_renamed_input(sum_table_renamed):
    sum_table_renamed['sum_squared'] = sum_table_renamed['sum'] * sum_table_renamed['sum']
    return sum_table_renamed


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
        get_num_csv_environment(get_load_only_solids_config('load_csv')),
    )
    assert isinstance(df, pd.DataFrame)
    assert df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def _sum_only_pipeline():
    return PipelineDefinition(
        solids=[sum_table, sum_sq_table],
        dependencies={},
    )


def test_two_input_solid():
    def transform(_context, inputs):
        num_csv1 = inputs['num_csv1']
        num_csv2 = inputs['num_csv2']
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

    df = pipeline_result.result_for_solid('two_input_solid').transformed_value()

    # df = get_solid_transformed_value(create_test_context(), two_input_solid, environment)
    assert isinstance(df, pd.DataFrame)
    assert df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def test_no_transform_solid():
    num_table = _dataframe_solid(
        name='num_table',
        inputs=[InputDefinition('num_csv', dagster_pd.DataFrame)],
        transform_fn=lambda _context, inputs: inputs['num_csv'],
    )
    context = create_test_context()
    df = get_solid_transformed_value(
        context, num_table, get_num_csv_environment(get_load_only_solids_config('load_csv'))
    )
    assert df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4]}


def create_diamond_pipeline(extra_solids=None, extra_dependencies=None):
    all_solids = list(create_diamond_dag()) + (extra_solids if extra_solids else [])
    all_deps = {}
    all_deps.update(create_diamond_deps())
    if extra_dependencies:
        all_deps.update(extra_dependencies)
    return PipelineDefinition(solids=all_solids, dependencies=all_deps)


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
        transform_fn=lambda _context, inputs: inputs['num_csv'],
    )

    def sum_transform(_context, inputs):
        num_df = inputs['num_table']
        sum_df = num_df.copy()
        sum_df['sum'] = num_df['num1'] + num_df['num2']
        return sum_df

    sum_table_solid = _dataframe_solid(
        name='sum_table',
        inputs=[InputDefinition('num_table', dagster_pd.DataFrame)],
        transform_fn=sum_transform,
    )

    def mult_transform(_context, inputs):
        num_table = inputs['num_table']
        mult_table = num_table.copy()
        mult_table['mult'] = num_table['num1'] * num_table['num2']
        return mult_table

    mult_table_solid = _dataframe_solid(
        name='mult_table',
        inputs=[InputDefinition('num_table', dagster_pd.DataFrame)],
        transform_fn=mult_transform,
    )

    def sum_mult_transform(_context, inputs):
        sum_df = inputs['sum_table']
        mult_df = inputs['mult_table']
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
        pipeline, environment=get_num_csv_environment(get_load_only_solids_config('load_csv'))
    )

    assert result.result_for_solid('sum_mult_table').transformed_value().to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
        'mult': [2, 12],
        'sum_mult': [6, 84],
    }


def test_pandas_output_csv_pipeline():
    with get_temp_file_name() as temp_file_name:
        write_solid = dagster_pd.to_csv_solid('write_sum_mult_table')
        pipeline = create_diamond_pipeline(
            extra_solids=[write_solid],
            extra_dependencies={write_solid.name: {
                'df': DependencyDefinition('sum_mult_table')
            }}
        )
        environment = get_num_csv_environment(
            {
                'load_csv': config.Solid({
                    'path': script_relative_path('num.csv'),
                }),
                write_solid.name: config.Solid({
                    'path': temp_file_name
                }),
            }
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


def _result_for_solid(results, name):
    for result in results:
        if result.name == name:
            return result

    check.failed('could not find name')


def test_pandas_output_intermediate_csv_files():

    with get_temp_file_names(2) as temp_tuple:
        sum_file, mult_file = temp_tuple  # pylint: disable=E0632

        write_sum_table = dagster_pd.to_csv_solid('write_sum_table')
        write_mult_table = dagster_pd.to_csv_solid('write_mult_table')

        pipeline = create_diamond_pipeline(
            extra_solids=[write_sum_table, write_mult_table],
            extra_dependencies={
                write_sum_table.name: {
                    'df': DependencyDefinition('sum_table'),
                },
                write_mult_table.name: {
                    'df': DependencyDefinition('mult_table'),
                }
            }
        )

        environment = get_num_csv_environment(
            {
                'load_csv': config.Solid({
                    'path': script_relative_path('num.csv'),
                }),
                write_sum_table.name: config.Solid({
                    'path': sum_file
                }),
                write_mult_table.name: config.Solid({
                    'path': mult_file
                }),
            }
        )

        subgraph_one_result = execute_pipeline(pipeline, environment=environment)

        assert len(subgraph_one_result.result_list) == 5

        expected_sum = {
            'num1': [1, 3],
            'num2': [2, 4],
            'sum': [3, 7],
        }

        assert pd.read_csv(sum_file).to_dict('list') == expected_sum
        sum_table_result = subgraph_one_result.result_for_solid('sum_table')
        assert sum_table_result.transformed_value().to_dict('list') == expected_sum

        expected_mult = {
            'num1': [1, 3],
            'num2': [2, 4],
            'mult': [2, 12],
        }
        assert pd.read_csv(mult_file).to_dict('list') == expected_mult
        mult_table_result = subgraph_one_result.result_for_solid('mult_table')
        assert mult_table_result.transformed_value().to_dict('list') == expected_mult

        injected_solids = {
            'sum_mult_table': {
                'sum_table': dagster_pd.load_csv_solid('load_sum_table'),
                'mult_table': dagster_pd.load_csv_solid('load_mult_table'),
            }
        }

        pipeline_result = execute_pipeline(
            PipelineDefinition.create_sub_pipeline(
                pipeline,
                ['sum_mult_table'],
                ['sum_mult_table'],
                injected_solids,
            ),
            environment=config.Environment(
                solids={
                    'load_sum_table': config.Solid({
                        'path': sum_file
                    }, ),
                    'load_mult_table': config.Solid({
                        'path': mult_file
                    }, ),
                },
            ),
        )

        assert pipeline_result.success

        subgraph_two_result_list = pipeline_result.result_list

        assert len(subgraph_two_result_list) == 3
        output_df = pipeline_result.result_for_solid('sum_mult_table').transformed_value()
        assert output_df.to_dict('list') == {
            'num1': [1, 3],
            'num2': [2, 4],
            'sum': [3, 7],
            'mult': [2, 12],
            'sum_mult': [6, 84],
        }


def test_pandas_output_intermediate_parquet_files():
    pipeline = create_diamond_pipeline()

    with get_temp_file_names(2) as temp_tuple:
        # false positive on pylint error
        sum_file, mult_file = temp_tuple  # pylint: disable=E0632

        write_sum_table = dagster_pd.to_parquet_solid('write_sum_table')
        write_mult_table = dagster_pd.to_parquet_solid('write_mult_table')

        pipeline = create_diamond_pipeline(
            extra_solids=[write_sum_table, write_mult_table],
            extra_dependencies={
                write_sum_table.name: {
                    'df': DependencyDefinition('sum_table'),
                },
                write_mult_table.name: {
                    'df': DependencyDefinition('mult_table'),
                }
            }
        )

        environment = get_num_csv_environment(
            {
                'load_csv': config.Solid({
                    'path': script_relative_path('num.csv'),
                }),
                write_sum_table.name: config.Solid({
                    'path': sum_file
                }),
                write_mult_table.name: config.Solid({
                    'path': mult_file
                }),
            }
        )

        pipeline_result = execute_pipeline(
            pipeline,
            environment,
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
    )

    def transform_fn(_context, inputs):
        return inputs['num_csv1'] + inputs['num_csv2']

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
    ).result_for_solid('double_sum').transformed_value()

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

        write_sum_mult_csv = dagster_pd.to_csv_solid('write_sum_mult_csv')
        write_sum_mult_parquet = dagster_pd.to_parquet_solid('write_sum_mult_parquet')

        pipeline = create_diamond_pipeline(
            extra_solids=[write_sum_mult_csv, write_sum_mult_parquet],
            extra_dependencies={
                write_sum_mult_csv.name: {
                    'df': DependencyDefinition('sum_mult_table'),
                },
                write_sum_mult_parquet.name: {
                    'df': DependencyDefinition('sum_mult_table'),
                }
            }
        )

        environment = get_num_csv_environment(
            {
                'load_csv': config.Solid({
                    'path': script_relative_path('num.csv'),
                }),
                write_sum_mult_csv.name: config.Solid({
                    'path': csv_file,
                }),
                write_sum_mult_parquet.name: config.Solid({
                    'path': parquet_file,
                }),
            }
        )

        execute_pipeline(pipeline, environment)

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
        environment=get_num_csv_environment(get_load_only_solids_config('load_csv')),
    )

    assert result.success

    expected = {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
        'sum_squared': [9, 49],
    }
    solid_result = result.result_for_solid('sum_sq_table_renamed_input')
    assert solid_result.transformed_value().to_dict('list') == expected
