import pandas as pd

import check

from solidic.definitions import (
    SolidInputDefinition, SolidOutputTypeDefinition, Solid, create_solidic_single_file_input
)
from solidic.types import (SolidPath, SolidString)


def create_solid_pandas_dependency_input(solid):
    check.inst_param(solid, 'solid', Solid)

    def dependency_input_fn(arg_dict):
        path = check.str_elem(arg_dict, 'path')
        frmt = check.str_elem(arg_dict, 'format')

        if frmt == 'CSV':
            return pd.read_csv(path)
        elif frmt == 'PARQUET':
            return pd.read_parquet(path)
        else:
            check.not_implemented('Format {frmt} not supported'.format(frmt=frmt))

    return SolidInputDefinition(
        name=solid.name,
        input_fn=dependency_input_fn,
        argument_def_dict={
            'path': SolidPath,
            'format': SolidString,
        },
        depends_on=solid,
    )


def create_solidic_pandas_csv_input(name, delimiter=',', **read_csv_kwargs):
    check.str_param(name, 'name')
    check.str_param(delimiter, 'delimiter')

    def check_path(path):
        check.str_param(path, 'path')
        return pd.read_csv(path, delimiter=delimiter, **read_csv_kwargs)

    return create_solidic_single_file_input(name, check_path)


def create_solidic_pandas_csv_output():
    def output_fn_inst(df, output_arg_dict):
        check.inst_param(df, 'df', pd.DataFrame)
        check.dict_param(output_arg_dict, 'output_arg_dict')
        path = check.str_elem(output_arg_dict, 'path')

        df.to_csv(path, index=False)

    return SolidOutputTypeDefinition(
        name='CSV', output_fn=output_fn_inst, argument_def_dict={'path': SolidPath}
    )


def create_solidic_pandas_parquet_output():
    def output_fn_inst(df, output_arg_dict):
        check.inst_param(df, 'df', pd.DataFrame)
        check.dict_param(output_arg_dict, 'output_arg_dict')
        path = check.str_elem(output_arg_dict, 'path')

        df.to_parquet(path)

    return SolidOutputTypeDefinition(
        name='PARQUET', output_fn=output_fn_inst, argument_def_dict={'path': SolidPath}
    )
