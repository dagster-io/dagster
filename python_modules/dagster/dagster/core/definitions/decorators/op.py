from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Union

from dagster import check
from dagster.utils.backcompat import experimental_decorator

from ..input import In, InputDefinition
from ..output import MultiOut, Out, OutputDefinition
from ..policy import RetryPolicy
from ..solid import SolidDefinition
from .solid import _Solid, solid


@experimental_decorator
def op(
    name: Union[Callable[..., Any], Optional[str]] = None,
    description: Optional[str] = None,
    input_defs: Optional[List[InputDefinition]] = None,
    output_defs: Optional[List[OutputDefinition]] = None,
    config_schema: Optional[Union[Any, Dict[str, Any]]] = None,
    required_resource_keys: Optional[Set[str]] = None,
    tags: Optional[Dict[str, Any]] = None,
    version: Optional[str] = None,
    retry_policy: Optional[RetryPolicy] = None,
    ins: Optional[List[In]] = None,
    out: Optional[Union[Out, MultiOut]] = None,
) -> Union[_Solid, SolidDefinition]:
    """Op is an experimental replacement for solid, intended to decrease verbosity of core API."""
    if input_defs is not None and ins is not None:
        check.failed("Values cannot be provided for both the 'input_defs' and 'ins' arguments")

    if output_defs is not None and out is not None:
        check.failed("Values cannot be provided for both the 'output_defs' and 'out' arguments")

    final_output_defs: Optional[Sequence[OutputDefinition]] = None
    if out:
        check.inst_param(out, "out", (Out, MultiOut))

        if isinstance(out, Out):
            final_output_defs = [out]
        elif isinstance(out, MultiOut):
            final_output_defs = out.outs
    else:
        final_output_defs = output_defs

    return solid(
        name=name,
        description=description,
        input_defs=input_defs or ins,
        output_defs=final_output_defs,
        config_schema=config_schema,
        required_resource_keys=required_resource_keys,
        tags=tags,
        version=version,
        retry_policy=retry_policy,
    )
