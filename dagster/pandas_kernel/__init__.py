from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *  # pylint: disable=W0622,W0401
import inspect

import pandas as pd

from dagster import check
from dagster.utils import has_context_argument

from dagster.core import create_json_input
from dagster.core.definitions import Solid, OutputDefinition
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


def _default_passthrough_transform(*args, **kwargs):
    check.invariant(not args, 'There should be no positional args')
    check.invariant(len(kwargs) == 1, 'There should be only one input')
    return list(kwargs.values())[0]


def _post_process_transform(context, df):
    check.inst_param(context, 'context', DagsterExecutionContext)
    check.inst_param(df, 'df', pd.DataFrame)

    context.metric('rows', df.shape[0])


def _check_transform_output(df, name):
    if not isinstance(df, pd.DataFrame):
        raise DagsterInvariantViolationError(
            f'Transform function of dataframe solid {name} ' + \
            f'did not return a dataframe. Got {repr(df)}'
        )


def _dependency_transform_wrapper(name, transform_fn):
    check.callable_param(transform_fn, 'transform_fn')
    if has_context_argument(transform_fn):

        def wrapper_with_context(context, **kwargs):
            df = transform_fn(context=context, **kwargs)
            _check_transform_output(df, name)
            _post_process_transform(context, df)
            return df

        return wrapper_with_context
    else:

        def wrapper_no_context(context, **kwargs):
            df = transform_fn(**kwargs)
            _check_transform_output(df, name)
            _post_process_transform(context, df)
            return df

        return wrapper_no_context


def dataframe_solid(*args, name, inputs, transform_fn=None, materializations=None, **kwargs):
    check.invariant(not args, 'must use all keyword args')

    # will add parquet and other standardized formats
    if transform_fn is None:
        check.param_invariant(
            len(inputs) == 1, 'inputs',
            'If you do not specify a transform there must only be one input'
        )
        transform_fn = _default_passthrough_transform
    else:
        validate_transform_fn(name, transform_fn, inputs)

    if not materializations:
        materializations = [dataframe_csv_materialization(), dataframe_parquet_materialization()]

    output = OutputDefinition(materializations=materializations)

    return Solid(
        name=name,
        inputs=inputs,
        transform_fn=_dependency_transform_wrapper(name, transform_fn),
        output=output,
        **kwargs
    )


def single_path_arg(input_name, path):
    check.str_param(input_name, 'input_name')
    check.str_param(path, 'path')
    return {input_name: {'path': path}}


def json_input(name):
    return create_json_input(name)


# XXX(freiksenet): this should really go to main solid file
def validate_transform_fn(solid_name, transform_fn, inputs):
    input_names = set(inp.name for inp in inputs)
    used_inputs = set()
    has_kwargs = False

    signature = inspect.signature(transform_fn)
    for i, param in enumerate(signature.parameters.values()):
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            has_kwargs = True
        elif param.kind == inspect.Parameter.VAR_POSITIONAL:
            raise DagsterInvalidDefinitionError(
                f"solid '{solid_name}' transform function has positional vararg parameter '{param.name}'. Transform functions should only have keyword arguments that match input names and optionally a first positional parameter named 'context'."
            )
        else:
            # XXX(freiksenet): I don't like this
            if param.name == 'context':
                pass
            elif param.name not in input_names:
                raise DagsterInvalidDefinitionError(
                    f"solid '{solid_name}' transform function has parameter '{param.name}' that is not one of the solid inputs. Transform functions should only have keyword arguments that match input names and optionally a first positional parameter named 'context'."
                )
            else:
                used_inputs.add(param.name)

    undeclared_inputs = input_names - used_inputs
    if not has_kwargs and undeclared_inputs:
        undeclared_inputs_printed = ", '".join(undeclared_inputs)
        raise DagsterInvalidDefinitionError(
            f"solid '{solid_name}' transform function do not have parameter(s) '{undeclared_inputs_printed}', which are in solid's inputs. Transform functions should only have keyword arguments that match input names and optionally a first positional parameter named 'context'."
        )
