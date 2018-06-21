from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *  # pylint: disable=W0622,W0401

import pandas as pd

from dagster import check
from dagster.utils import has_context_argument

from dagster.core import create_json_input
from dagster.core.definitions import Solid, OutputDefinition, ExpectationDefinition, ExpectationResult
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
)


def _default_passthrough_transform(context, arguments):
    return list(arguments.values())[0]


def _post_process_transform(context, df):
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(df, 'df', pd.DataFrame)

    context.metric('rows', df.shape[0])


def _check_transform_output(df):
    if not isinstance(df, pd.DataFrame):
        return ExpectationResult(
          success=False,
          message=f'Transform function of dataframe solid ' + \
            f"did not return a dataframe. Got '{repr(df)}'"

        )
    else:
        return ExpectationResult(success=True)


def dataframe_output_expectation():
    return ExpectationDefinition(name='DataframeOutput', expectation_fn=_check_transform_output)


def dataframe_output(materializations=None):
    if materializations is None:
        materializations = [dataframe_csv_materialization(), dataframe_parquet_materialization()]

    return OutputDefinition(
        materializations=materializations, expectations=[dataframe_output_expectation()]
    )


def dataframe_solid(*args, name, inputs, transform_fn=None, materializations=None, **kwargs):
    check.invariant(not args, 'must use all keyword args')

    # will add parquet and other standardized formats
    if transform_fn is None:
        transform_fn = _default_passthrough_transform

    output = dataframe_output(materializations)

    return Solid(name=name, inputs=inputs, transform_fn=transform_fn, output=output, **kwargs)


def single_path_arg(input_name, path):
    check.str_param(input_name, 'input_name')
    check.str_param(path, 'path')
    return {input_name: {'path': path}}


def json_input(name):
    return create_json_input(name)
