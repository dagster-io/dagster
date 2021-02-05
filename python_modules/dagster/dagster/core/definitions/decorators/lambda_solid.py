from functools import update_wrapper, wraps
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Union

from dagster import check
from dagster.core.types.dagster_type import DagsterTypeKind

from ..events import Output
from ..inference import infer_input_definitions_for_lambda_solid, infer_output_definitions
from ..input import InputDefinition
from ..output import OutputDefinition
from ..solid import SolidDefinition
from .solid import validate_solid_fn

if TYPE_CHECKING:
    from dagster.core.execution.context.compute import SolidExecutionContext


class _LambdaSolid:
    def __init__(
        self,
        name: Optional[str] = None,
        input_defs: Optional[List[InputDefinition]] = None,
        output_def: Optional[OutputDefinition] = None,
        description: Optional[str] = None,
    ):
        self.name = check.opt_str_param(name, "name")
        self.input_defs = check.opt_nullable_list_param(input_defs, "input_defs", InputDefinition)
        self.output_def = check.opt_inst_param(output_def, "output_def", OutputDefinition)
        self.description = check.opt_str_param(description, "description")

    def __call__(self, fn: Callable[..., Any]) -> SolidDefinition:
        check.callable_param(fn, "fn")

        if not self.name:
            self.name = fn.__name__

        input_defs = (
            self.input_defs
            if self.input_defs is not None
            else infer_input_definitions_for_lambda_solid(self.name, fn)
        )
        output_def = (
            self.output_def
            if self.output_def is not None
            else infer_output_definitions("@lambda_solid", self.name, fn)[0]
        )

        positional_inputs = validate_solid_fn("@lambda_solid", self.name, fn, input_defs)
        compute_fn = _create_lambda_solid_compute_wrapper(fn, input_defs, output_def)

        solid_def = SolidDefinition(
            name=self.name,
            input_defs=input_defs,
            output_defs=[output_def],
            compute_fn=compute_fn,
            description=self.description,
            positional_inputs=positional_inputs,
        )
        update_wrapper(solid_def, fn)
        return solid_def


def lambda_solid(
    name: Union[Optional[str], Callable[..., Any]] = None,
    description: Optional[str] = None,
    input_defs: Optional[List[InputDefinition]] = None,
    output_def: Optional[OutputDefinition] = None,
) -> Union[_LambdaSolid, SolidDefinition]:
    """Create a simple solid from the decorated function.

    This shortcut allows the creation of simple solids that do not require
    configuration and whose implementations do not require a
    :py:class:`context <SystemComputeExecutionContext>`.

    Lambda solids take any number of inputs and produce a single output.

    Inputs can be defined using :class:`InputDefinition` and passed to the ``input_defs`` argument
    of this decorator, or inferred from the type signature of the decorated function.

    The single output can be defined using :class:`OutputDefinition` and passed as the
    ``output_def`` argument of this decorator, or its type can be inferred from the type signature
    of the decorated function.

    The body of the decorated function should return a single value, which will be yielded as the
    solid's output.

    Args:
        name (str): Name of solid.
        description (str): Solid description.
        input_defs (List[InputDefinition]): List of input_defs.
        output_def (OutputDefinition): The output of the solid. Defaults to
            :class:`OutputDefinition() <OutputDefinition>`.

    Examples:

    .. code-block:: python

        @lambda_solid
        def hello_world():
            return 'hello'

        @lambda_solid(
            input_defs=[InputDefinition(name='foo', str)],
            output_def=OutputDefinition(str)
        )
        def hello_world(foo):
            # explicitly type and name inputs and outputs
            return foo

        @lambda_solid
        def hello_world(foo: str) -> str:
            # same as above inferred from signature
            return foo

    """
    if callable(name):
        check.invariant(input_defs is None)
        check.invariant(description is None)
        return _LambdaSolid(output_def=output_def)(name)

    return _LambdaSolid(
        name=name, input_defs=input_defs, output_def=output_def, description=description
    )


def _create_lambda_solid_compute_wrapper(
    fn: Callable[..., Any], input_defs: List[InputDefinition], output_def: OutputDefinition
) -> Callable[["SolidExecutionContext", List[InputDefinition]], Any]:
    check.callable_param(fn, "fn")
    check.list_param(input_defs, "input_defs", of_type=InputDefinition)
    check.inst_param(output_def, "output_def", OutputDefinition)

    input_names = [
        input_def.name
        for input_def in input_defs
        if not input_def.dagster_type.kind == DagsterTypeKind.NOTHING
    ]

    @wraps(fn)
    def compute(_context: "SolidExecutionContext", input_defs: List[InputDefinition]) -> Any:
        kwargs = {}
        for input_name in input_names:
            kwargs[input_name] = input_defs[input_name]

        result = fn(**kwargs)
        yield Output(value=result, output_name=output_def.name)

    return compute
