import inspect
from typing import Any, Callable, Dict, List, NamedTuple, Optional

from dagster._seven import funcsigs, is_module_available

from .utils import NoValueSentinel


class InferredInputProps(NamedTuple):
    """The information about an input that can be inferred from the function signature"""

    name: str
    annotation: Any
    description: Optional[str]
    default_value: Any = NoValueSentinel


class InferredOutputProps(NamedTuple):
    """The information about an input that can be inferred from the function signature"""

    annotation: Any
    description: Optional[str]


def _infer_input_description_from_docstring(fn: Callable) -> Dict[str, Optional[str]]:
    doc_str = fn.__doc__
    if not is_module_available("docstring_parser") or doc_str is None:
        return {}

    from docstring_parser import parse

    try:
        docstring = parse(doc_str)
        return {p.arg_name: p.description for p in docstring.params}
    except Exception:
        return {}


def _infer_output_description_from_docstring(fn: Callable) -> Optional[str]:
    doc_str = fn.__doc__
    if not is_module_available("docstring_parser") or doc_str is None:
        return None
    from docstring_parser import parse

    try:
        docstring = parse(doc_str)
        if docstring.returns is None:
            return None

        return docstring.returns.description
    except Exception:
        return None


def infer_output_props(fn: Callable) -> InferredOutputProps:
    signature = funcsigs.signature(fn)

    annotation = inspect.Parameter.empty
    if not inspect.isgeneratorfunction(fn):
        annotation = signature.return_annotation

    return InferredOutputProps(
        annotation=annotation,
        description=_infer_output_description_from_docstring(fn),
    )


def has_explicit_return_type(fn: Callable) -> bool:
    signature = funcsigs.signature(fn)
    return not signature.return_annotation is funcsigs.Signature.empty


def _infer_inputs_from_params(
    params: List[funcsigs.Parameter],
    descriptions: Optional[Dict[str, Optional[str]]] = None,
) -> List[InferredInputProps]:
    descriptions: Dict[str, Optional[str]] = descriptions or {}
    input_defs = []
    for param in params:
        if param.default is not funcsigs.Parameter.empty:
            input_def = InferredInputProps(
                param.name,
                param.annotation,
                default_value=param.default,
                description=descriptions.get(param.name),
            )
        else:
            input_def = InferredInputProps(
                param.name,
                param.annotation,
                description=descriptions.get(param.name),
            )

        input_defs.append(input_def)

    return input_defs


def infer_input_props(fn: Callable, context_arg_provided: bool) -> List[InferredInputProps]:
    signature = funcsigs.signature(fn)
    params = list(signature.parameters.values())
    descriptions = _infer_input_description_from_docstring(fn)
    params_to_infer = params[1:] if context_arg_provided else params
    defs = _infer_inputs_from_params(params_to_infer, descriptions=descriptions)
    return defs
