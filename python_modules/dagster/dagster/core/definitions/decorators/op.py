from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Union

from dagster import check
from dagster.utils.backcompat import experimental_decorator

from ..inference import infer_output_props
from ..input import In, InputDefinition
from ..output import MultiOut, Out, OutputDefinition
from ..policy import RetryPolicy
from ..solid import SolidDefinition
from .solid import _Solid


class _Op:
    def __init__(
        self,
        name: Optional[str] = None,
        input_defs: Optional[Sequence[InputDefinition]] = None,
        output_defs: Optional[Sequence[OutputDefinition]] = None,
        description: Optional[str] = None,
        required_resource_keys: Optional[Set[str]] = None,
        config_schema: Optional[Union[Any, Dict[str, Any]]] = None,
        tags: Optional[Dict[str, Any]] = None,
        version: Optional[str] = None,
        decorator_takes_context: Optional[bool] = True,
        retry_policy: Optional[RetryPolicy] = None,
        ins: Optional[Dict[str, In]] = None,
        out: Optional[Union[Out, MultiOut]] = None,
    ):
        self.name = check.opt_str_param(name, "name")
        self.input_defs = input_defs
        self.output_defs = output_defs
        self.decorator_takes_context = check.bool_param(
            decorator_takes_context, "decorator_takes_context"
        )

        self.description = check.opt_str_param(description, "description")

        # these will be checked within SolidDefinition
        self.required_resource_keys = required_resource_keys
        self.tags = tags
        self.version = version
        self.retry_policy = retry_policy

        # config will be checked within SolidDefinition
        self.config_schema = config_schema

        self.ins = check.opt_dict_param(ins, "ins", key_type=str)
        self.out = out

    def __call__(self, fn: Callable[..., Any]) -> SolidDefinition:
        if self.input_defs is not None and self.ins is not None:
            check.failed("Values cannot be provided for both the 'input_defs' and 'ins' arguments")

        if self.output_defs is not None and self.out is not None:
            check.failed("Values cannot be provided for both the 'output_defs' and 'out' arguments")

        inferred_out = infer_output_props(fn)

        input_defs = [inp.to_definition(name) for name, inp in self.ins.items()]

        final_output_defs: Optional[Sequence[OutputDefinition]] = None
        if self.out:
            check.inst_param(self.out, "out", (Out, MultiOut))

            if isinstance(self.out, Out):
                final_output_defs = [self.out.to_definition(inferred_out)]
            elif isinstance(self.out, MultiOut):
                final_output_defs = self.out.to_definition_list(inferred_out)
        else:
            final_output_defs = self.output_defs

        return _Solid(
            name=self.name,
            input_defs=self.input_defs or input_defs,
            output_defs=final_output_defs,
            description=self.description,
            required_resource_keys=self.required_resource_keys,
            config_schema=self.config_schema,
            tags=self.tags,
            version=self.version,
            decorator_takes_context=self.decorator_takes_context,
            retry_policy=self.retry_policy,
        )(fn)


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
    ins: Optional[Dict[str, In]] = None,
    out: Optional[Union[Out, MultiOut]] = None,
) -> Union[_Op, SolidDefinition]:
    """Op is an experimental replacement for solid, intended to decrease verbosity of core API."""
    # This case is for when decorator is used bare, without arguments. e.g. @op versus @op()
    if callable(name):
        check.invariant(input_defs is None)
        check.invariant(output_defs is None)
        check.invariant(description is None)
        check.invariant(config_schema is None)
        check.invariant(required_resource_keys is None)
        check.invariant(tags is None)
        check.invariant(version is None)

        return _Op()(name)

    return _Op(
        name=name,
        description=description,
        input_defs=input_defs,
        output_defs=output_defs,
        config_schema=config_schema,
        required_resource_keys=required_resource_keys,
        tags=tags,
        version=version,
        retry_policy=retry_policy,
        ins=ins,
        out=out,
    )
