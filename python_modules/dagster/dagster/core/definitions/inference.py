import inspect
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Type

from dagster.check import CheckError
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.seven import funcsigs, is_module_available

from .output import OutputDefinition
from .utils import NoValueSentinel


class InferredInputProps(NamedTuple):
    """The information about an input that can be inferred from the function signature"""

    name: str
    python_type: Optional[Type]
    description: Optional[str]
    default_value: Any = NoValueSentinel


def _infer_input_description_from_docstring(fn: Callable) -> Dict[str, Optional[str]]:
    if not is_module_available("docstring_parser"):
        return {}

    from docstring_parser import parse

    docstring = parse(fn.__doc__)
    return {p.arg_name: p.description for p in docstring.params}


def _infer_output_description_from_docstring(fn: Callable) -> Optional[str]:
    if not is_module_available("docstring_parser"):
        return None
    from docstring_parser import parse

    docstring = parse(fn.__doc__)
    if docstring.returns is None:
        return None

    return docstring.returns.description


def infer_output_definitions(
    decorator_name: str, solid_name: str, fn: Callable
) -> List[OutputDefinition]:
    signature = funcsigs.signature(fn)
    try:
        description = _infer_output_description_from_docstring(fn)
        return [
            OutputDefinition()
            if signature.return_annotation is funcsigs.Signature.empty
            else OutputDefinition(signature.return_annotation, description=description)
        ]

    except CheckError as type_error:
        raise DagsterInvalidDefinitionError(
            "Error inferring Dagster type for return type "
            f'"{signature.return_annotation}" from {decorator_name} "{solid_name}". '
            f"Correct the issue or explicitly pass definitions to {decorator_name}."
        ) from type_error


def has_explicit_return_type(fn: Callable) -> bool:
    signature = funcsigs.signature(fn)
    return not signature.return_annotation is funcsigs.Signature.empty


def _input_param_type(type_annotation: Type) -> Optional[Type]:
    if type_annotation is not inspect.Parameter.empty:
        return type_annotation
    return None


def _infer_inputs_from_params(
    params: List[funcsigs.Parameter],
    decorator_name: str,
    solid_name: str,
    descriptions: Optional[Dict[str, Optional[str]]] = None,
) -> List[InferredInputProps]:
    descriptions: Dict[str, Optional[str]] = descriptions or {}
    input_defs = []
    for param in params:
        try:
            if param.default is not funcsigs.Parameter.empty:
                input_def = InferredInputProps(
                    param.name,
                    _input_param_type(param.annotation),
                    default_value=param.default,
                    description=descriptions.get(param.name),
                )
            else:
                input_def = InferredInputProps(
                    param.name,
                    _input_param_type(param.annotation),
                    description=descriptions.get(param.name),
                )

            input_defs.append(input_def)

        except CheckError as type_error:
            raise DagsterInvalidDefinitionError(
                f"Error inferring Dagster type for input name {param.name} typed as "
                f'"{param.annotation}" from {decorator_name} "{solid_name}". '
                "Correct the issue or explicitly pass definitions to {decorator_name}."
            ) from type_error

    return input_defs


def infer_input_props(
    decorator_name: str, fn_name: str, fn: Callable, has_context_arg: bool
) -> List[InferredInputProps]:
    signature = funcsigs.signature(fn)
    params = list(signature.parameters.values())
    descriptions = _infer_input_description_from_docstring(fn)
    params_to_infer = params[1:] if has_context_arg else params
    defs = _infer_inputs_from_params(
        params_to_infer, decorator_name, fn_name, descriptions=descriptions
    )
    return defs
