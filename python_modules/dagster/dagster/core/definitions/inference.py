import inspect
import sys

import six

from dagster.check import CheckError
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.types.dagster_type import resolve_dagster_type
from dagster.seven import funcsigs, is_module_available

from .input import InputDefinition, _NoValueSentinel
from .output import OutputDefinition


def infer_output_definitions(decorator_name, solid_name, fn):
    signature = funcsigs.signature(fn)
    try:
        # try to infer from docstring
        defs = _infer_output_definitions_from_docstring(solid_name, fn)

        if defs is None:
            defs = [
                OutputDefinition()
                if signature.return_annotation is funcsigs.Signature.empty
                else OutputDefinition(signature.return_annotation)
            ]

        return defs
    except CheckError as type_error:
        six.raise_from(
            DagsterInvalidDefinitionError(
                'Error inferring Dagster type for return type '
                '"{type_annotation}" from {decorator} "{solid}". '
                'Correct the issue or explicitly pass definitions to {decorator}.'.format(
                    decorator=decorator_name,
                    solid=solid_name,
                    type_annotation=signature.return_annotation,
                )
            ),
            type_error,
        )


def has_explicit_return_type(fn):
    signature = funcsigs.signature(fn)
    return not signature.return_annotation is funcsigs.Signature.empty


def _input_param_type(type_annotation):
    if sys.version_info.major >= 3 and type_annotation is not inspect.Parameter.empty:
        return type_annotation
    return None


def infer_input_definitions_for_lambda_solid(solid_name, fn):
    signature = funcsigs.signature(fn)
    params = list(signature.parameters.values())

    return _infer_inputs_from_params(params, '@lambda_solid', solid_name)


def _infer_output_definitions_from_docstring(solid_name, fn):
    if not is_module_available("docstring_parser"):
        return

    from docstring_parser import parse

    docstring = parse(fn.__doc__)

    if docstring.returns is None:
        return

    type_name = docstring.returns.type_name
    name = docstring.returns.return_name or "result"

    try:
        ttype = eval(type_name)
    except NameError as type_error:
        six.raise_from(
            DagsterInvalidDefinitionError(
                'Error inferring Dagster type for return type '
                '"{type_name}" from @solid "{solid}". '
                'Correct the issue or explicitly pass definitions to @solid.'.format(
                    type_name=type_name, solid=solid_name,
                )
            ),
            type_error,
        )

    dtype = resolve_dagster_type(ttype)
    description = docstring.returns.description
    output_def = OutputDefinition(name=name, dagster_type=dtype, description=description)
    return [output_def]


def _infer_input_definitions_from_docstring(solid_name, fn):
    if not is_module_available("docstring_parser"):
        return

    from docstring_parser import parse

    docstring = parse(fn.__doc__)

    params = {}
    input_defs = []

    for p in docstring.params:
        try:
            name = p.arg_name
            ttype = eval(p.type_name)
            default = _NoValueSentinel

            if p.default != "None":
                default = ttype(p.default)

            description = p.description

            dtype = resolve_dagster_type(ttype)

            input_def = InputDefinition(name, dtype, description, default)
            input_defs.append(input_def)
        except (NameError, ValueError) as type_error:
            six.raise_from(
                DagsterInvalidDefinitionError(
                    'Error infering dagster type from docstring param {param} typed '
                    'as {param_type} from @solid "{solid}". '
                    'Correct the issue or explicitly pass definitions to @solid'.format(
                        param=p.arg_name, param_type=p.type_name, solid=solid_name,
                    )
                ),
                type_error,
            )

    if not input_defs:
        return None

    return input_defs


def _infer_inputs_from_params(params, decorator_name, solid_name):
    input_defs = []
    for param in params:
        try:
            if param.default is not funcsigs.Parameter.empty:
                input_def = InputDefinition(
                    param.name, _input_param_type(param.annotation), default_value=param.default
                )
            else:
                input_def = InputDefinition(param.name, _input_param_type(param.annotation))

            input_defs.append(input_def)

        except CheckError as type_error:
            six.raise_from(
                DagsterInvalidDefinitionError(
                    'Error inferring Dagster type for input name {param} typed as '
                    '"{type_annotation}" from {decorator} "{solid}". '
                    'Correct the issue or explicitly pass definitions to {decorator}.'.format(
                        decorator=decorator_name,
                        solid=solid_name,
                        param=param.name,
                        type_annotation=param.annotation,
                    )
                ),
                type_error,
            )

    return input_defs


def infer_input_definitions_for_composite_solid(solid_name, fn):
    # try to infer from docstrings
    defs = _infer_input_definitions_from_docstring(solid_name, fn)

    if defs is None:
        signature = funcsigs.signature(fn)
        params = list(signature.parameters.values())
        defs = _infer_inputs_from_params(params, '@composite_solid', solid_name)

    return defs


def infer_input_definitions_for_solid(solid_name, fn):
    # try to infer from docstrings
    defs = _infer_input_definitions_from_docstring(solid_name, fn)

    if defs is None:
        signature = funcsigs.signature(fn)
        params = list(signature.parameters.values())
        defs = _infer_inputs_from_params(params[1:], '@solid', solid_name)

    return defs
