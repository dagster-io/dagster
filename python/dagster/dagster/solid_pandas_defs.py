import pandas as pd

import check

from .solid_defs import SolidInputDefinition
from .solid_types import SolidPath


def create_solid_pandas_csv_input(name):
    return SolidInputDefinition(
        name=name,
        input_fn=lambda arg_dict: pd.read_csv(check.str_elem(arg_dict, 'path')),
        argument_def_dict={'path': SolidPath}
    )
