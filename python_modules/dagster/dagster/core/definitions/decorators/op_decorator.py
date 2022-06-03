from functools import update_wrapper
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    Union,
    overload,
)

import dagster._check as check
from dagster.config.config_schema import ConfigSchemaType
from dagster.core.decorator_utils import format_docstring_for_description

from ....seven.typing import get_origin
from ...errors import DagsterInvariantViolationError
from ..inference import InferredOutputProps, infer_output_props
from ..input import In, InputDefinition
from ..output import Out, OutputDefinition
from ..policy import RetryPolicy
from ..solid_definition import SolidDefinition
from .solid_decorator import (
    DecoratedSolidFunction,
    NoContextDecoratedSolidFunction,
    resolve_checked_solid_fn_inputs,
)

if TYPE_CHECKING:
    from ..op_definition import OpDefinition


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
        out: Optional[Union[Out, Dict[str, Out]]] = None,
    ):
        self.name = check.opt_str_param(name, "name")
        self.input_defs = check.opt_nullable_sequence_param(
            input_defs, "input_defs", of_type=InputDefinition
        )
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

        self.ins = check.opt_nullable_dict_param(ins, "ins", key_type=str, value_type=In)
        self.out = out

    def __call__(self, fn: Callable[..., Any]) -> "OpDefinition":
        from ..op_definition import OpDefinition

        if self.input_defs is not None and self.ins is not None:
            check.failed("Values cannot be provided for both the 'input_defs' and 'ins' arguments")

        if self.output_defs is not None and self.out is not None:
            check.failed("Values cannot be provided for both the 'output_defs' and 'out' arguments")

        inferred_out = infer_output_props(fn)

        if self.ins is not None:
            input_defs = [
                inp.to_definition(name)
                for name, inp in sorted(self.ins.items(), key=lambda input: input[0])
            ]  # sort so that input definition order is deterministic
        else:
            input_defs = check.opt_list_param(
                self.input_defs, "input_defs", of_type=InputDefinition
            )

        output_defs_from_out = _resolve_output_defs_from_outs(
            inferred_out=inferred_out, out=self.out
        )
        resolved_output_defs = (
            output_defs_from_out if output_defs_from_out is not None else self.output_defs
        )

        if not self.name:
            self.name = fn.__name__

        if resolved_output_defs is None:
            resolved_output_defs = [OutputDefinition.create_from_inferred(infer_output_props(fn))]
        elif len(resolved_output_defs) == 1:
            resolved_output_defs = [
                resolved_output_defs[0].combine_with_inferred(infer_output_props(fn))
            ]

        compute_fn = (
            DecoratedSolidFunction(decorated_fn=fn)
            if self.decorator_takes_context
            else NoContextDecoratedSolidFunction(decorated_fn=fn)
        )

        resolved_input_defs = resolve_checked_solid_fn_inputs(
            decorator_name="@op",
            fn_name=self.name,
            compute_fn=compute_fn,
            explicit_input_defs=input_defs,
            exclude_nothing=True,
        )

        op_def = OpDefinition(
            name=self.name,
            input_defs=resolved_input_defs,
            output_defs=resolved_output_defs,
            compute_fn=compute_fn,
            config_schema=self.config_schema,
            description=self.description or format_docstring_for_description(fn),
            required_resource_keys=self.required_resource_keys,
            tags=self.tags,
            version=self.version,
            retry_policy=self.retry_policy,
        )
        update_wrapper(op_def, compute_fn.decorated_fn)
        return op_def


def _resolve_output_defs_from_outs(
    inferred_out: InferredOutputProps, out: Optional[Union[Out, dict]]
) -> Optional[List[OutputDefinition]]:
    if out is None:
        return None
    if isinstance(out, Out):
        return [out.to_definition(inferred_out.annotation, name=None)]
    else:
        check.dict_param(out, "out", key_type=str, value_type=Out)

        # If only a single entry has been provided to the out dict, then slurp the
        # annotation into the entry.
        if len(out) == 1:
            name = list(out.keys())[0]
            only_out = out[name]
            return [only_out.to_definition(inferred_out.annotation, name)]

        output_defs = []

        # Introspection on type annotations is experimental, so checking
        # metaclass is the best we can do.
        if inferred_out.annotation and not get_origin(inferred_out.annotation) == tuple:
            raise DagsterInvariantViolationError(
                "Expected Tuple annotation for multiple outputs, but received non-tuple annotation."
            )
        if inferred_out.annotation and not len(inferred_out.annotation.__args__) == len(out):
            raise DagsterInvariantViolationError(
                "Expected Tuple annotation to have number of entries matching the "
                f"number of outputs for more than one output. Expected {len(out)} "
                f"outputs but annotation has {len(inferred_out.annotation.__args__)}."
            )
        for idx, (name, cur_out) in enumerate(out.items()):
            annotation_type = (
                inferred_out.annotation.__args__[idx] if inferred_out.annotation else None
            )
            output_defs.append(cur_out.to_definition(annotation_type, name=name))

        return output_defs


@overload
def op(name: Callable[..., Any]) -> SolidDefinition:
    ...


@overload
def op(
    name: Optional[str] = ...,
    description: Optional[str] = ...,
    ins: Optional[Dict[str, In]] = ...,
    out: Optional[Union[Out, Dict[str, Out]]] = ...,
    config_schema: Optional[ConfigSchemaType] = ...,
    required_resource_keys: Optional[Set[str]] = ...,
    tags: Optional[Dict[str, Any]] = ...,
    version: Optional[str] = ...,
    retry_policy: Optional[RetryPolicy] = ...,
    input_defs: Optional[List[InputDefinition]] = ...,
    output_defs: Optional[List[OutputDefinition]] = ...,
) -> _Op:
    ...


def op(
    name: Optional[Union[Callable[..., Any], str]] = None,
    description: Optional[str] = None,
    ins: Optional[Dict[str, In]] = None,
    out: Optional[Union[Out, Dict[str, Out]]] = None,
    config_schema: Optional[ConfigSchemaType] = None,
    required_resource_keys: Optional[Set[str]] = None,
    tags: Optional[Dict[str, Any]] = None,
    version: Optional[str] = None,
    retry_policy: Optional[RetryPolicy] = None,
    input_defs: Optional[List[InputDefinition]] = None,
    output_defs: Optional[List[OutputDefinition]] = None,
) -> Union[SolidDefinition, _Op]:
    """
    Create an op with the specified parameters from the decorated function.

    Ins and outs will be inferred from the type signature of the decorated function
    if not explicitly provided.

    The decorated function will be used as the op's compute function. The signature of the
    decorated function is more flexible than that of the ``compute_fn`` in the core API; it may:

    1. Return a value. This value will be wrapped in an :py:class:`Output` and yielded by the compute function.
    2. Return an :py:class:`Output`. This output will be yielded by the compute function.
    3. Yield :py:class:`Output` or other :ref:`event objects <events>`. Same as default compute behavior.

    Note that options 1) and 2) are incompatible with yielding other events -- if you would like
    to decorate a function that yields events, it must also wrap its eventual output in an
    :py:class:`Output` and yield it.

    @op supports ``async def`` functions as well, including async generators when yielding multiple
    events or outputs. Note that async ops will generally be run on their own unless using a custom
    :py:class:`Executor` implementation that supports running them together.

    Args:
        name (Optional[str]): Name of op. Must be unique within any :py:class:`GraphDefinition`
            using the op.
        description (Optional[str]): Human-readable description of this op. If not provided, and
            the decorated function has docstring, that docstring will be used as the description.
        ins (Optional[Dict[str, In]]):
            Information about the inputs to the op. Information provided here will be combined
            with what can be inferred from the function signature.
        out (Optional[Union[Out, Dict[str, Out]]]):
            Information about the op outputs. Information provided here will be combined with
            what can be inferred from the return type signature if the function does not use yield.
        config_schema (Optional[ConfigSchema): The schema for the config. If set, Dagster will check
            that config provided for the op matches this schema and fail if it does not. If not
            set, Dagster will accept any config provided for the op.
        required_resource_keys (Optional[Set[str]]): Set of resource handles required by this op.
        tags (Optional[Dict[str, Any]]): Arbitrary metadata for the op. Frameworks may
            expect and require certain metadata to be attached to a op. Values that are not strings
            will be json encoded and must meet the criteria that `json.loads(json.dumps(value)) == value`.
        version (Optional[str]): (Experimental) The version of the op's compute_fn. Two ops should have
            the same version if and only if they deterministically produce the same outputs when
            provided the same inputs.
        retry_policy (Optional[RetryPolicy]): The retry policy for this op.
        input_defs (Optional[List[InputDefinition]]):
            (legacy) Preserved to ease migration from :py:class:`solid`. Can be used in place of ins argument.
        output_defs (Optional[List[OutputDefinition]]):
            (legacy) Preserved to ease migration from :py:class:`solid`. Can be used in place of out argument.

    Examples:

        .. code-block:: python

            @op
            def hello_world():
                print('hello')

            @op
            def echo(msg: str) -> str:
                return msg

            @op(
                ins={'msg': In(str)},
                out=Out(str)
            )
            def echo_2(msg): # same as above
                return msg

            @op(
                out={'word': Out(), 'num': Out()}
            )
            def multi_out() -> Tuple[str, int]:
                return 'cool', 4
    """

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
