import pandas as pd

from dagster import check

from dagster.core.definitions import (
    Solid,
    create_dagster_single_file_input,
    InputDefinition,
    create_single_source_input,
    MaterializationDefinition,
    OutputDefinition,
)
from dagster.core.execution import DagsterExecutionContext

from dagster.core import types


def _read_df(path, frmt):
    if frmt == 'CSV':
        return pd.read_csv(path)
    elif frmt == 'PARQUET':
        return pd.read_parquet(path)
    else:
        check.not_implemented('Format {frmt} not supported'.format(frmt=frmt))


def create_dagster_pd_dependency_input(solid):
    check.inst_param(solid, 'solid', Solid)

    def dependency_input_fn(context, arg_dict):
        check.inst_param(context, 'context', DagsterExecutionContext)
        path = check.str_elem(arg_dict, 'path')
        frmt = check.str_elem(arg_dict, 'format')

        df = _read_df(path, frmt)

        context.metric('rows', df.shape[0])

        return df

    return create_single_source_input(
        name=solid.name,
        source_fn=dependency_input_fn,
        argument_def_dict={
            'path': types.PATH,
            'format': types.STRING,
        },
        depends_on=solid,
        source_type='CSVORPARQUET',
    )


def create_dagster_pd_csv_input(name, delimiter=',', **read_csv_kwargs):
    check.str_param(name, 'name')
    check.str_param(delimiter, 'delimiter')

    def check_path(context, path):
        check.inst_param(context, 'context', DagsterExecutionContext)
        check.str_param(path, 'path')
        df = pd.read_csv(path, delimiter=delimiter, **read_csv_kwargs)
        context.metric('rows', df.shape[0])
        return df

    return create_dagster_single_file_input(name, check_path, source_type='CSV')


def create_dagster_pd_read_table_input(name, delimiter=',', **read_table_kwargs):
    check.str_param(name, 'name')
    check.str_param(delimiter, 'delimiter')

    def check_path(context, path):
        check.inst_param(context, 'context', DagsterExecutionContext)
        check.str_param(path, 'path')
        df = pd.read_table(path, delimiter=delimiter, **read_table_kwargs)
        context.metric('rows', df.shape[0])
        return df

    return create_dagster_single_file_input(name, check_path, source_type='TABLE')


def create_dagster_pd_csv_materialization():
    def to_csv_fn(df, context, arg_dict):
        check.inst_param(df, 'df', pd.DataFrame)
        check.inst_param(context, 'context', DagsterExecutionContext)
        check.dict_param(arg_dict, 'arg_dict')
        path = check.str_elem(arg_dict, 'path')

        df.to_csv(path, index=False)

    return MaterializationDefinition(
        materialization_type='CSV',
        materialization_fn=to_csv_fn,
        argument_def_dict={'path': types.PATH}
    )


def create_dagster_pd_parquet_materialization():
    def to_parquet_fn(df, context, arg_dict):
        check.inst_param(df, 'df', pd.DataFrame)
        check.inst_param(context, 'context', DagsterExecutionContext)
        check.dict_param(arg_dict, 'arg_dict')
        path = check.str_elem(arg_dict, 'path')

        df.to_parquet(path)

    return MaterializationDefinition(
        materialization_type='PARQUET',
        materialization_fn=to_parquet_fn,
        argument_def_dict={'path': types.PATH}
    )


def create_dataframe_solid_output_definition():
    return OutputDefinition(
        materializations=[
            create_dagster_pd_csv_materialization(),
            create_dagster_pd_parquet_materialization(),
        ]
    )
