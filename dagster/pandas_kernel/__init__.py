from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *  # pylint: disable=W0622,W0401

import pandas as pd

from dagster import check
from dagster.utils import has_context_argument

from dagster.core import create_json_input
from dagster.core.definitions import SolidDefinition, OutputDefinition, ExpectationDefinition, ExpectationResult
from dagster.core.execution import DagsterExecutionContext
from dagster.core.errors import (
    DagsterUserCodeExecutionError, DagsterInvariantViolationError, DagsterInvalidDefinitionError
)
from .definitions import (
    dataframe_dependency,
    dataframe_input,
    parquet_dataframe_source,
    csv_dataframe_source,
    table_dataframe_source,
    dataframe_parquet_materialization,
    dataframe_csv_materialization,
    dataframe_output,
)


def _default_passthrough_transform(_context, arguments):
    check.invariant(len(arguments) == 1)
    return list(arguments.values())[0]


def dataframe_solid(*args, name, inputs, transform_fn=None, materializations=None, **kwargs):
    check.invariant(not args, 'must use all keyword args')

    # will add parquet and other standardized formats
    if transform_fn is None:
        transform_fn = _default_passthrough_transform

    output = dataframe_output(materializations)

    return SolidDefinition(
        name=name, inputs=inputs, transform_fn=transform_fn, output=output, **kwargs
    )


def single_path_arg(input_name, path):
    check.str_param(input_name, 'input_name')
    check.str_param(path, 'path')
    return {input_name: {'path': path}}


def json_input(name):
    return create_json_input(name)
