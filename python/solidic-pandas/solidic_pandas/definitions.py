import pandas as pd

import check

from solidic.definitions import (SolidInputDefinition, SolidOutputTypeDefinition)
from solidic.types import SolidPath


def create_solidic_pandas_csv_input(name):
    check.str_param(name, 'name')
    return SolidInputDefinition(
        name=name,
        input_fn=lambda arg_dict: pd.read_csv(check.str_elem(arg_dict, 'path')),
        argument_def_dict={'path': SolidPath}
    )


def create_solidic_pandas_csv_output():
    def output_fn_inst(df, output_arg_dict):
        check.inst_param(df, 'df', pd.DataFrame)
        check.dict_param(output_arg_dict, 'output_arg_dict')
        path = check.str_elem(output_arg_dict, 'path')

        df.to_csv(path, index=False)

    return SolidOutputTypeDefinition(
        name='CSV', output_fn=output_fn_inst, argument_def_dict={'path': SolidPath}
    )
