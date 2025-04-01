from collections.abc import Mapping, Sequence
from functools import lru_cache, update_wrapper
from inspect import Parameter
from typing import (  # noqa: UP035
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    NamedTuple,
    Optional,
    Union,
    cast,
    overload,
)

import dagster._check as check
from dagster._annotations import deprecated_param
from dagster._config import UserConfigSchema
from dagster._core.decorator_utils import (
    format_docstring_for_description,
    get_function_params,
    get_valid_name_permutations,
    param_is_var_keyword,
    positional_arg_name_list,
)
from dagster._core.definitions.inference import infer_input_props
from dagster._core.definitions.input import In, InputDefinition
from dagster._core.definitions.output import Out
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.definitions.resource_annotation import get_resource_args
from dagster._core.definitions.utils import DEFAULT_OUTPUT
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.types.dagster_type import DagsterTypeKind
from dagster._utils.warnings import config_argument_warning, normalize_renamed_param

if TYPE_CHECKING:
    from dagster._core.definitions.op_definition import OpDefinition


class _Op:
    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        required_resource_keys: Optional[AbstractSet[str]] = None,
        config_schema: Optional[Union[Any, Mapping[str, Any]]] = None,
        tags: Optional[Mapping[str, Any]] = None,
        code_version: Optional[str] = None,
        decorator_takes_context: Optional[bool] = True,
        retry_policy: Optional[RetryPolicy] = None,
        ins: Optional[Mapping[str, In]] = None,
        out: Optional[Union[Out, Mapping[str, Out]]] = None,
        pool: Optional[str] = None,
    ):
        self.name = check.opt_str_param(name, "name")
        self.decorator_takes_context = check.bool_param(
            decorator_takes_context, "decorator_takes_context"
        )

        self.description = check.opt_str_param(description, "description")

        # these will be checked within OpDefinition
        self.required_resource_keys = required_resource_keys
        self.tags = tags
        self.code_version = code_version
        self.retry_policy = retry_policy
        self.pool = pool

        # config will be checked within OpDefinition
        self.config_schema = config_schema

        self.ins = check.opt_nullable_mapping_param(ins, "ins", key_type=str, value_type=In)
        self.out = out

    def __call__(self, fn: Callable[..., Any]) -> "OpDefinition":
        from dagster._config.pythonic_config import validate_resource_annotated_function
        from dagster._core.definitions.op_definition import OpDefinition

        validate_resource_annotated_function(fn)

        if not self.name:
            self.name = fn.__name__

        compute_fn = (
            DecoratedOpFunction(decorated_fn=fn)
            if self.decorator_takes_context
            else NoContextDecoratedOpFunction(decorated_fn=fn)
        )

        compute_fn.validate_malformed_config()

        if compute_fn.has_config_arg():
            check.param_invariant(
                self.config_schema is None or self.config_schema == {},
                "If the @op has a config arg, you cannot specify a config schema",
            )

            from dagster._config.pythonic_config import infer_schema_from_config_annotation

            # Parse schema from the type annotation of the config arg
            config_arg = compute_fn.get_config_arg()
            config_arg_type = config_arg.annotation
            config_arg_default = config_arg.default
            self.config_schema = infer_schema_from_config_annotation(
                config_arg_type, config_arg_default
            )

        outs: Optional[Mapping[str, Out]] = None
        if self.out is not None and isinstance(self.out, Out):
            outs = {DEFAULT_OUTPUT: self.out}
        elif self.out is not None:
            outs = check.mapping_param(self.out, "out", key_type=str, value_type=Out)

        arg_resource_keys = {arg.name for arg in compute_fn.get_resource_args()}
        decorator_resource_keys = set(self.required_resource_keys or [])
        check.param_invariant(
            len(decorator_resource_keys) == 0 or len(arg_resource_keys) == 0,
            "Cannot specify resource requirements in both @op decorator and as arguments to the"
            " decorated function",
        )
        resolved_resource_keys = decorator_resource_keys.union(arg_resource_keys)

        op_def = OpDefinition.dagster_internal_init(
            name=self.name,
            ins=self.ins,
            outs=outs,
            compute_fn=compute_fn,
            config_schema=self.config_schema,
            description=self.description or format_docstring_for_description(fn),
            required_resource_keys=resolved_resource_keys,
            tags=self.tags,
            code_version=self.code_version,
            retry_policy=self.retry_policy,
            version=None,  # code_version has replaced version
            pool=self.pool,
        )
        update_wrapper(op_def, compute_fn.decorated_fn)
        return op_def


@overload
def op(compute_fn: Callable[..., Any]) -> "OpDefinition": ...


@overload
def op(
    *,
    name: Optional[str] = ...,
    description: Optional[str] = ...,
    ins: Optional[Mapping[str, In]] = ...,
    out: Optional[Union[Out, Mapping[str, Out]]] = ...,
    config_schema: Optional[UserConfigSchema] = ...,
    required_resource_keys: Optional[AbstractSet[str]] = ...,
    tags: Optional[Mapping[str, Any]] = ...,
    version: Optional[str] = ...,
    retry_policy: Optional[RetryPolicy] = ...,
    code_version: Optional[str] = ...,
    pool: Optional[str] = None,
) -> _Op: ...


@deprecated_param(
    param="version", breaking_version="2.0", additional_warn_text="Use `code_version` instead"
)
def op(
    compute_fn: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    ins: Optional[Mapping[str, In]] = None,
    out: Optional[Union[Out, Mapping[str, Out]]] = None,
    config_schema: Optional[UserConfigSchema] = None,
    required_resource_keys: Optional[AbstractSet[str]] = None,
    tags: Optional[Mapping[str, Any]] = None,
    version: Optional[str] = None,
    retry_policy: Optional[RetryPolicy] = None,
    code_version: Optional[str] = None,
    pool: Optional[str] = None,
) -> Union["OpDefinition", _Op]:
    """Create an op with the specified parameters from the decorated function.

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
        code_version (Optional[str]): Version of the logic encapsulated by the op. If set,
            this is used as a default version for all outputs.
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
    code_version = normalize_renamed_param(
        code_version,
        "code_version",
        version,
        "version",
    )

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
        code_version=code_version,
        retry_policy=retry_policy,
        ins=ins,
        out=out,
        pool=pool,
    )


class DecoratedOpFunction(NamedTuple):
    """Wrapper around the decorated op function to provide commonly used util methods."""

    decorated_fn: Callable[..., Any]

    @property
    def name(self):
        return self.decorated_fn.__name__

    @lru_cache(maxsize=1)
    def has_context_arg(self) -> bool:
        return is_context_provided(get_function_params(self.decorated_fn))

    def get_context_arg(self) -> Parameter:
        if self.has_context_arg():
            return get_function_params(self.decorated_fn)[0]
        check.failed("Requested context arg on function that does not have one")

    @lru_cache(maxsize=1)
    def _get_function_params(self) -> Sequence[Parameter]:
        return get_function_params(self.decorated_fn)

    def has_config_arg(self) -> bool:
        for param in get_function_params(self.decorated_fn):
            if param.name == "config":
                return True

        return False

    def validate_malformed_config(self) -> None:
        from dagster._config.pythonic_config.config import Config
        from dagster._config.pythonic_config.type_check_utils import safe_is_subclass

        positional_inputs = self.positional_inputs()
        for param in get_function_params(self.decorated_fn):
            if safe_is_subclass(param.annotation, Config) and param.name in positional_inputs:
                config_argument_warning(param.name, self.name)

    def get_config_arg(self) -> Parameter:
        for param in get_function_params(self.decorated_fn):
            if param.name == "config":
                return param

        check.failed("Requested config arg on function that does not have one")

    def get_resource_args(self) -> Sequence[Parameter]:
        return get_resource_args(self.decorated_fn)

    def positional_inputs(self) -> Sequence[str]:
        params = self._get_function_params()
        input_args = params[1:] if self.has_context_arg() else params
        resource_arg_names = [arg.name for arg in self.get_resource_args()]
        input_args_filtered = [
            input_arg
            for input_arg in input_args
            if input_arg.name != "config" and input_arg.name not in resource_arg_names
        ]
        return positional_arg_name_list(input_args_filtered)

    def has_var_kwargs(self) -> bool:
        params = self._get_function_params()
        # var keyword arg has to be the last argument
        return len(params) > 0 and param_is_var_keyword(params[-1])

    def get_output_annotation(self) -> Any:
        from dagster._core.definitions.inference import infer_output_props

        return infer_output_props(self.decorated_fn).annotation


class NoContextDecoratedOpFunction(DecoratedOpFunction):
    """Wrapper around a decorated op function, when the decorator does not permit a context
    parameter.
    """

    @lru_cache(maxsize=1)
    def has_context_arg(self) -> bool:
        return False


def is_context_provided(params: Sequence[Parameter]) -> bool:
    if len(params) == 0:
        return False
    return params[0].name in get_valid_name_permutations("context")


def resolve_checked_op_fn_inputs(
    decorator_name: str,
    fn_name: str,
    compute_fn: DecoratedOpFunction,
    explicit_input_defs: Sequence[InputDefinition],
    exclude_nothing: bool,
) -> Sequence[InputDefinition]:
    """Validate provided input definitions and infer the remaining from the type signature of the compute_fn.
    Returns the resolved set of InputDefinitions.

    Args:
        decorator_name (str): Name of the decorator that is wrapping the op function.
        fn_name (str): Name of the decorated function.
        compute_fn (DecoratedOpFunction): The decorated function, wrapped in the
            DecoratedOpFunction wrapper.
        explicit_input_defs (List[InputDefinition]): The input definitions that were explicitly
            provided in the decorator.
        exclude_nothing (bool): True if Nothing type inputs should be excluded from compute_fn
            arguments.
    """
    explicit_names = set()
    if exclude_nothing:
        explicit_names = set(
            inp.name
            for inp in explicit_input_defs
            if not inp.dagster_type.kind == DagsterTypeKind.NOTHING
        )
        nothing_names = set(
            inp.name
            for inp in explicit_input_defs
            if inp.dagster_type.kind == DagsterTypeKind.NOTHING
        )
    else:
        explicit_names = set(inp.name for inp in explicit_input_defs)
        nothing_names = set()

    params = get_function_params(compute_fn.decorated_fn)

    input_args = params[1:] if compute_fn.has_context_arg() else params

    # filter out config arg
    resource_arg_names = {arg.name for arg in compute_fn.get_resource_args()}
    explicit_names = explicit_names - resource_arg_names

    if compute_fn.has_config_arg() or resource_arg_names:
        new_input_args = []
        for input_arg in input_args:
            if input_arg.name != "config" and input_arg.name not in resource_arg_names:
                new_input_args.append(input_arg)
        input_args = new_input_args

    # Validate input arguments
    used_inputs = set()
    inputs_to_infer = set()
    has_kwargs = False

    for param in cast(list[Parameter], input_args):
        if param.kind == Parameter.VAR_KEYWORD:
            has_kwargs = True
        elif param.kind == Parameter.VAR_POSITIONAL:
            raise DagsterInvalidDefinitionError(
                f"{decorator_name} '{fn_name}' decorated function has positional vararg parameter "
                f"'{param}'. {decorator_name} decorated functions should only have keyword "
                "arguments that match input names and, if system information is required, a first "
                "positional parameter named 'context'."
            )

        else:
            if param.name not in explicit_names:
                if param.name in nothing_names:
                    raise DagsterInvalidDefinitionError(
                        f"{decorator_name} '{fn_name}' decorated function has parameter"
                        f" '{param.name}' that is one of the input_defs of type 'Nothing' which"
                        " should not be included since no data will be passed for it. "
                    )
                else:
                    inputs_to_infer.add(param.name)

            else:
                used_inputs.add(param.name)

    undeclared_inputs = explicit_names - used_inputs
    if not has_kwargs and undeclared_inputs:
        undeclared_inputs_printed = ", '".join(undeclared_inputs)
        nothing_exemption = (
            ", except for Ins that have the Nothing dagster_type"
            if decorator_name not in {"@graph", "@graph_asset"}
            else ""
        )
        raise DagsterInvalidDefinitionError(
            f"{decorator_name} '{fn_name}' decorated function does not have argument(s)"
            f" '{undeclared_inputs_printed}'. {decorator_name}-decorated functions should have an"
            f" argument for each of their Ins{nothing_exemption}. Alternatively, they can"
            " accept **kwargs."
        )

    inferred_props = {
        inferred.name: inferred
        for inferred in infer_input_props(compute_fn.decorated_fn, compute_fn.has_context_arg())
    }
    input_defs = []
    for input_def in explicit_input_defs:
        if input_def.name in inferred_props:
            # combine any information missing on the explicit def that can be inferred
            input_defs.append(input_def.combine_with_inferred(inferred_props[input_def.name]))
        else:
            # pass through those that don't have any inference info, such as Nothing type inputs
            input_defs.append(input_def)

    # build defs from the inferred props for those without explicit entries
    inferred_input_defs = [
        InputDefinition.create_from_inferred(inferred)
        for inferred in inferred_props.values()
        if inferred.name in inputs_to_infer
    ]

    if exclude_nothing:
        for in_def in inferred_input_defs:
            if in_def.dagster_type.is_nothing:
                raise DagsterInvalidDefinitionError(
                    f"Input parameter {in_def.name} is annotated with"
                    f" {in_def.dagster_type.display_name} which is a type that represents passing"
                    " no data. This type must be used via In() and no parameter should be included"
                    f" in the {decorator_name} decorated function."
                )

    input_defs.extend(inferred_input_defs)

    return input_defs
