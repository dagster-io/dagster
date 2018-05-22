import pandas as pd

from dagster import check

from dagster.solidic.definitions import (
    SolidInputDefinition, SolidOutputDefinition, Solid, create_solidic_single_file_input
)
from dagster.solidic.execution import SolidExecutionContext
from dagster.solidic.types import (SolidPath, SolidString)


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
        check.inst_param(context, 'context', SolidExecutionContext)
        path = check.str_elem(arg_dict, 'path')
        frmt = check.str_elem(arg_dict, 'format')

        df = _read_df(path, frmt)

        context.metric('rows', df.shape[0])

        return df

    return SolidInputDefinition(
        name=solid.name,
        input_fn=dependency_input_fn,
        argument_def_dict={
            'path': SolidPath,
            'format': SolidString,
        },
        depends_on=solid,
    )


def create_dagster_pd_csv_input(name, delimiter=',', **read_csv_kwargs):
    check.str_param(name, 'name')
    check.str_param(delimiter, 'delimiter')

    def check_path(context, path):
        check.inst_param(context, 'context', SolidExecutionContext)
        check.str_param(path, 'path')
        df = pd.read_csv(path, delimiter=delimiter, **read_csv_kwargs)
        context.metric('rows', df.shape[0])
        return df

    return create_solidic_single_file_input(name, check_path)


def create_dagster_pd_csv_output():
    def output_fn_inst(df, context, arg_dict):
        check.inst_param(df, 'df', pd.DataFrame)
        check.inst_param(context, 'context', SolidExecutionContext)
        check.dict_param(arg_dict, 'arg_dict')
        path = check.str_elem(arg_dict, 'path')

        df.to_csv(path, index=False)

    return SolidOutputDefinition(
        name='CSV', output_fn=output_fn_inst, argument_def_dict={'path': SolidPath}
    )


def create_dagster_pd_parquet_output():
    def output_fn_inst(df, context, arg_dict):
        check.inst_param(df, 'df', pd.DataFrame)
        check.inst_param(context, 'context', SolidExecutionContext)
        check.dict_param(arg_dict, 'arg_dict')
        path = check.str_elem(arg_dict, 'path')

        df.to_parquet(path)

    return SolidOutputDefinition(
        name='PARQUET', output_fn=output_fn_inst, argument_def_dict={'path': SolidPath}
    )
