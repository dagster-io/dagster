from functools import update_wrapper
from typing import TYPE_CHECKING, Any, Callable, Dict, Mapping, Optional, Set, Union, overload

import dagster._check as check
from dagster._config import UserConfigSchema
from dagster._core.decorator_utils import format_docstring_for_description

from ..input import In
from ..output import Out
from ..policy import RetryPolicy
from ..utils import DEFAULT_OUTPUT
from .solid_decorator import DecoratedSolidFunction, NoContextDecoratedSolidFunction

if TYPE_CHECKING:
    from ..op_definition import OpDefinition


class _Op:
    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        required_resource_keys: Optional[Set[str]] = None,
        config_schema: Optional[Union[Any, Dict[str, Any]]] = None,
        tags: Optional[Dict[str, Any]] = None,
        version: Optional[str] = None,
        decorator_takes_context: Optional[bool] = True,
        retry_policy: Optional[RetryPolicy] = None,
        ins: Optional[Dict[str, In]] = None,
        out: Optional[Union[Out, Mapping[str, Out]]] = None,
    ):
        self.name = check.opt_str_param(name, "name")
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

        if not self.name:
            self.name = fn.__name__

        compute_fn = (
            DecoratedSolidFunction(decorated_fn=fn)
            if self.decorator_takes_context
            else NoContextDecoratedSolidFunction(decorated_fn=fn)
        )

        outs: Optional[Mapping[str, Out]] = None
        if self.out is not None and isinstance(self.out, Out):
            outs = {DEFAULT_OUTPUT: self.out}
        elif self.out is not None:
            outs = check.mapping_param(self.out, "out", key_type=str, value_type=Out)

        op_def = OpDefinition(
            name=self.name,
            ins=self.ins,
            outs=outs,
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


@overload
def op(compute_fn: Callable[..., Any]) -> "OpDefinition":
    ...


@overload
def op(
    *,
    name: Optional[str] = ...,
    description: Optional[str] = ...,
    ins: Optional[Dict[str, In]] = ...,
    out: Optional[Union[Out, Dict[str, Out]]] = ...,
    config_schema: Optional[UserConfigSchema] = ...,
    required_resource_keys: Optional[Set[str]] = ...,
    tags: Optional[Dict[str, Any]] = ...,
    version: Optional[str] = ...,
    retry_policy: Optional[RetryPolicy] = ...,
) -> _Op:
    ...


def op(
    compute_fn: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    ins: Optional[Dict[str, In]] = None,
    out: Optional[Union[Out, Mapping[str, Out]]] = None,
    config_schema: Optional[UserConfigSchema] = None,
    required_resource_keys: Optional[Set[str]] = None,
    tags: Optional[Dict[str, Any]] = None,
    version: Optional[str] = None,
    retry_policy: Optional[RetryPolicy] = None,
) -> Union["OpDefinition", _Op]:
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

    if compute_fn is not None:
        check.invariant(description is None)
        check.invariant(config_schema is None)
        check.invariant(required_resource_keys is None)
        check.invariant(tags is None)
        check.invariant(version is None)

        return _Op()(compute_fn)

    return _Op(
        name=name,
        description=description,
        config_schema=config_schema,
        required_resource_keys=required_resource_keys,
        tags=tags,
        version=version,
        retry_policy=retry_policy,
        ins=ins,
        out=out,
    )
