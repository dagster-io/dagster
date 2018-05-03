from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *  # pylint: disable=W0622,W0401

import check

from solidic.definitions import Solid
from .definitions import (
    create_solidic_pandas_csv_input, create_solidic_pandas_csv_output,
    create_solid_pandas_dependency_input
)


def solid(**kwargs):
    return Solid(**kwargs)


def dependency_input(solid_inst):
    check.inst_param(solid_inst, 'solid_inst', Solid)
    return create_solid_pandas_dependency_input(solid_inst)


def tabular_solid(**kwargs):
    # will add parquet and other standardized formats
    return Solid(output_type_defs=[csv_output()], **kwargs)


def single_path_arg(input_name, path):
    check.str_param(input_name, 'input_name')
    check.str_param(path, 'path')
    return {input_name: {'path': path}}


def csv_input(name):
    return create_solidic_pandas_csv_input(name)


def csv_output():
    return create_solidic_pandas_csv_output()
