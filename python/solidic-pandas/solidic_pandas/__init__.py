from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *  # pylint: disable=W0622,W0401

import check

from solidic.definitions import Solid
from .definitions import (
    create_solidic_pandas_csv_input,
    create_solidic_pandas_csv_output,
    create_solid_pandas_dependency_input,
    create_solidic_pandas_parquet_output,
)


def solid(**kwargs):
    return Solid(**kwargs)


def depends_on(solid_inst):
    check.inst_param(solid_inst, 'solid_inst', Solid)
    return create_solid_pandas_dependency_input(solid_inst)


def _default_passthrough_transform(*args, **kwargs):
    check.invariant(not args, 'There should be no positional args')
    check.invariant(len(kwargs) == 1, 'There should be only one input')
    return list(kwargs.values())[0]


def dataframe_solid(*args, inputs, transform_fn=None, **kwargs):
    check.invariant(not args, 'must use all keyword args')

    # will add parquet and other standardized formats
    if transform_fn is None:
        check.param_invariant(
            len(inputs) == 1, 'inputs',
            'If you do not specify a transform there must only be one input'
        )
        transform_fn = _default_passthrough_transform

    return Solid(
        inputs=inputs,
        output_type_defs=[csv_output(), parquet_output()],
        transform_fn=transform_fn,
        **kwargs
    )


def single_path_arg(input_name, path):
    check.str_param(input_name, 'input_name')
    check.str_param(path, 'path')
    return {input_name: {'path': path}}


def csv_input(name):
    return create_solidic_pandas_csv_input(name)


def csv_output():
    return create_solidic_pandas_csv_output()


def parquet_output():
    return create_solidic_pandas_parquet_output()
