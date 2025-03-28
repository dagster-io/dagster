import collections.abc
import sys
from collections.abc import Iterable, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from typing import (
    Annotated,
    Any,
    Callable,
    ForwardRef,
    Generic,
    Literal,
    NamedTuple,
    Optional,
    TypeVar,
    Union,
    get_args,
    get_origin,
)

from dagster_shared.check.functions import CheckError, TypeOrTupleOfTypes, failed, invariant

try:
    # this type only exists in python 3.10+
    from types import UnionType  # type: ignore
except ImportError:
    UnionType = Union

NoneType = type(None)

_contextual_ns: ContextVar[Mapping[str, type]] = ContextVar("_contextual_ns", default={})
INJECTED_DEFAULT_VALS_LOCAL_VAR = "__injected_defaults__"


class ImportFrom(NamedTuple):
    """A pointer to where to lazily import from to resolve a ForwardRef.

    Used with Annotated ie: Annotated['Foo', ImportFrom('baz.bar')]
    """

    module: str


class _LazyImportPlaceholder: ...


class EvalContext(NamedTuple):
    """Utility class for managing references to global and local namespaces.

    These namespaces are passed to ForwardRef._evaluate to resolve the actual
    type from a string.
    """

    global_ns: dict
    local_ns: dict
    lazy_imports: dict

    @staticmethod
    def capture_from_frame(
        depth: int,
        *,
        add_to_local_ns: Optional[Mapping[str, Any]] = None,
    ) -> "EvalContext":
        """Capture the global and local namespaces via the stack frame.

        Args:
            depth: which stack frame to reference, with depth 0 being the callsite.
            add_to_local_ns: A mapping of additional values to update the local namespace with.

        """
        ctx_frame = sys._getframe(depth + 1)  # noqa # surprisingly not costly

        # copy to not mess up frame data
        global_ns = ctx_frame.f_globals.copy()
        local_ns = ctx_frame.f_locals.copy()

        if add_to_local_ns:
            local_ns.update(add_to_local_ns)

        return EvalContext(
            global_ns=global_ns,
            local_ns=local_ns,
            lazy_imports={},
        )

    @staticmethod
    @contextmanager
    def contextual_namespace(ns: Mapping[str, type]):
        token = _contextual_ns.set(ns)
        try:
            yield
        finally:
            _contextual_ns.reset(token)

    def update_from_frame(self, depth: int):
        # Update the global and local namespaces with symbols from the target frame
        ctx_frame = sys._getframe(depth + 1)  # noqa # surprisingly not costly
        self.global_ns.update(ctx_frame.f_globals)
        self.local_ns.update(ctx_frame.f_locals)

    def register_lazy_import(self, type_name: str, module: str):
        invariant(
            self.lazy_imports.get(type_name, module) == module,
            f"Conflict in lazy imports for type {type_name}, tried to overwrite "
            f"{self.lazy_imports.get(type_name)} with {module}.",
        )
        self.lazy_imports[type_name] = module

    def get_merged_ns(self):
        return {
            **_contextual_ns.get(),
            **self.global_ns,
            **self.local_ns,
        }

    def eval_forward_ref(self, ref: ForwardRef) -> Optional[type]:
        if ref.__forward_arg__ in self.lazy_imports:
            # if we are going to add a lazy import for the type,
            # return a placeholder to grab the name from
            return type(ref.__forward_arg__, (_LazyImportPlaceholder,), {})
        try:
            if sys.version_info <= (3, 9):
                return ref._evaluate(  # noqa # type: ignore
                    globalns=self.get_merged_ns(),
                    localns={},
                )
            else:
                return ref._evaluate(  # noqa
                    globalns=self.get_merged_ns(),
                    localns={},
                    recursive_guard=frozenset(),
                )
        except NameError as e:
            raise CheckError(
                f"Unable to resolve {ref}, could not map string name to actual type using captured frames. "
                f"Use Annotated['{ref.__forward_arg__}', ImportFrom('module.to.import.from')] to create a lazy import."
            ) from e

    def compile_fn(self, body: str, fn_name: str) -> Callable:
        local_ns = {}
        exec(
            body,
            self.get_merged_ns(),
            local_ns,
        )
        return local_ns[fn_name]


T = TypeVar("T")


class _GenClass(Generic[T]): ...


# use a sample to avoid direct private imports (_GenericAlias)
_SampleGeneric = _GenClass[str]


def _coerce_type(
    ttype: Optional[TypeOrTupleOfTypes],
    eval_ctx: EvalContext,
) -> Optional[TypeOrTupleOfTypes]:
    # coerce input type in to the type we want to pass to the check call

    # Any type translates to passing None for the of_type argument
    if ttype is Any or ttype is None:
        return None

    # assume naked strings should be ForwardRefs
    if isinstance(ttype, str):
        return eval_ctx.eval_forward_ref(ForwardRef(ttype))

    if isinstance(ttype, ForwardRef):
        return eval_ctx.eval_forward_ref(ttype)

    if isinstance(ttype, TypeVar):
        return _coerce_type(ttype.__bound__, eval_ctx) if ttype.__bound__ else None

    origin = get_origin(ttype)
    args = get_args(ttype)

    if _is_annotated(origin, args):
        _process_annotated(ttype, args, eval_ctx)
        return _coerce_type(args[0], eval_ctx)

    # cant do isinstance against TypeDict (and we cant subclass check for it)
    # so just coerce any dict subclasses in to dict
    if isinstance(ttype, type) and issubclass(ttype, dict):
        return dict

    # Unions should become a tuple of types to pass to the of_type argument
    # ultimately used as second arg in isinstance(target, tuple_of_types)
    if origin in (UnionType, Union):
        union_types = get_args(ttype)
        coerced_types = []
        for t in union_types:
            # coerce all the inner types
            coerced = _coerce_type(t, eval_ctx)
            if coerced is None or isinstance(coerced, tuple):
                failed(f"Unable to coerce Union member {t} in {ttype}")
            coerced_types.append(coerced)

        return tuple(t for t in coerced_types)

    return ttype


def _container_pair_args(
    args: tuple[type, ...], eval_ctx
) -> tuple[Optional[TypeOrTupleOfTypes], Optional[TypeOrTupleOfTypes]]:
    # process tuple of types as if its two arguments to a container type

    if len(args) == 2:
        return _coerce_type(args[0], eval_ctx), _coerce_type(args[1], eval_ctx)

    return None, None


def _container_single_arg(
    args: tuple[type, ...], eval_ctx: EvalContext
) -> Optional[TypeOrTupleOfTypes]:
    # process tuple of types as if its the single argument to a container type

    if len(args) == 1:
        return _coerce_type(args[0], eval_ctx)

    return None


def _name(target: Optional[TypeOrTupleOfTypes]) -> str:
    # turn a type or tuple of types in to its string representation for printing

    if target is None:
        return "None"

    if target is NoneType:
        return "check.NoneType"

    if isinstance(target, tuple):
        return f"({', '.join(_name(tup_type) for tup_type in target)})"

    if hasattr(target, "__name__"):
        return target.__name__

    if hasattr(target, "_name"):
        n = getattr(target, "_name")
        if n is not None:
            return n

    # If a generic falls through to here, just target the base class
    # and ignore the type hint (for now).
    # Use a sample generic to avoid custom py version handling
    if target.__class__ is _SampleGeneric.__class__:
        return _name(get_origin(target))

    failed(f"Could not calculate string name for {target}")


def _is_annotated(origin, args):
    # 3.9+: origin is Annotated, 3.8: origin == args[0]
    return (origin is Annotated and args) or (len(args) == 1 and args[0] == origin)


def _process_annotated(ttype, args, eval_ctx: EvalContext):
    target_type = args[0]
    # 3.9+: args[1:] has Annotated args, 3.8: its in __metadata__
    annotated_args = getattr(ttype, "__metadata__", args[1:])
    for arg in annotated_args:
        if isinstance(arg, ImportFrom):
            if isinstance(target_type, ForwardRef):
                eval_ctx.register_lazy_import(args[0].__forward_arg__, arg.module)
            elif isinstance(target_type, str):
                eval_ctx.register_lazy_import(args[0], arg.module)
            else:
                failed(
                    f"ImportFrom in Annotated expected to be used with string or ForwardRef only, got {args[0]}",
                )


def build_check_call_str(
    ttype: type,
    name: str,
    eval_ctx: EvalContext,
) -> str:
    from dagster_shared.record import is_record

    # assumes this module is in global/local scope as check
    origin = get_origin(ttype)
    args = get_args(ttype)

    # scalars
    if origin is None:
        if ttype is str:
            return f'{name} if isinstance({name}, str) else check.str_param({name}, "{name}")'
        elif ttype is float:
            return f'{name} if isinstance({name}, float) else check.float_param({name}, "{name}")'
        elif ttype is int:
            return f'{name} if isinstance({name}, int) else check.int_param({name}, "{name}")'
        elif ttype is bool:
            return f'{name} if isinstance({name}, bool) else check.bool_param({name}, "{name}")'
        elif ttype is Any:
            return name  # no-op

        # fallback to inst
        inst_type = _coerce_type(ttype, eval_ctx)
        if inst_type:
            it = _name(inst_type)
            return (
                f'{name} if isinstance({name}, {it}) else check.inst_param({name}, "{name}", {it})'
            )
        else:
            return name  # no-op
    elif origin is Literal:
        return f'check.literal_param({name}, "{name}", {args})'
    elif origin is Callable or origin is collections.abc.Callable:
        return f'check.callable_param({name}, "{name}")'
    else:
        if _is_annotated(origin, args):
            _process_annotated(ttype, args, eval_ctx)
            return build_check_call_str(args[0], f"{name}", eval_ctx)

        pair_left, pair_right = _container_pair_args(args, eval_ctx)
        single = _container_single_arg(args, eval_ctx)

        # containers
        if origin is list:
            return f'check.list_param({name}, "{name}", {_name(single)})'
        elif origin is dict:
            return f'check.dict_param({name}, "{name}", {_name(pair_left)}, {_name(pair_right)})'
        elif origin is set:
            return f'check.set_param({name}, "{name}", {_name(single)})'
        elif origin is collections.abc.Sequence:
            return f'check.sequence_param({name}, "{name}", {_name(single)})'
        elif origin is collections.abc.Iterable:
            return f'check.iterable_param({name}, "{name}", {_name(single)})'
        elif origin is collections.abc.Mapping:
            return f'check.mapping_param({name}, "{name}", {_name(pair_left)}, {_name(pair_right)})'
        elif origin is collections.abc.Set:
            return f'check.set_param({name}, "{name}", {_name(single)})'
        elif origin in (UnionType, Union):
            # optional
            if pair_right is type(None):
                inner_origin = get_origin(pair_left)
                # optional scalar
                if inner_origin is None:
                    if pair_left is str:
                        return f'{name} if {name} is None or isinstance({name}, str) else check.opt_str_param({name}, "{name}")'
                    elif pair_left is float:
                        return f'{name} if {name} is None or isinstance({name}, float) else check.opt_float_param({name}, "{name}")'
                    elif pair_left is int:
                        return f'{name} if {name} is None or isinstance({name}, int) else check.opt_int_param({name}, "{name}")'
                    elif pair_left is bool:
                        return f'{name} if {name} is None or isinstance({name}, bool) else check.opt_bool_param({name}, "{name}")'

                    # fallback to opt_inst
                    inst_type = _coerce_type(pair_left, eval_ctx)
                    it = _name(inst_type)
                    if inst_type:
                        return f'{name} if {name} is None or isinstance({name}, {it}) else check.opt_inst_param({name}, "{name}", {it})'
                    else:
                        return name  # no-op

                # optional container
                else:
                    inner_args = get_args(pair_left)
                    inner_pair_left, inner_pair_right = _container_pair_args(inner_args, eval_ctx)
                    inner_single = _container_single_arg(inner_args, eval_ctx)
                    if inner_origin is list:
                        return f'{name} if {name} is None else check.opt_nullable_list_param({name}, "{name}", {_name(inner_single)})'
                    elif inner_origin is dict:
                        return f'{name} if {name} is None else check.opt_nullable_dict_param({name}, "{name}", {_name(inner_pair_left)}, {_name(inner_pair_right)})'
                    elif inner_origin is set:
                        return f'{name} if {name} is None else check.opt_nullable_set_param({name}, "{name}", {_name(inner_single)})'
                    elif inner_origin is collections.abc.Sequence:
                        return f'{name} if {name} is None else check.opt_nullable_sequence_param({name}, "{name}", {_name(inner_single)})'
                    elif inner_origin is collections.abc.Iterable:
                        return f'{name} if {name} is None else check.opt_nullable_iterable_param({name}, "{name}", {_name(inner_single)})'
                    elif inner_origin is collections.abc.Mapping:
                        return f'{name} if {name} is None else check.opt_nullable_mapping_param({name}, "{name}", {_name(inner_pair_left)}, {_name(inner_pair_right)})'
                    elif inner_origin is collections.abc.Set:
                        return f'{name} if {name} is None else check.opt_nullable_set_param({name}, "{name}", {_name(inner_single)})'
                    elif is_record(inner_origin):
                        it = _name(inner_origin)
                        return f'{name} if {name} is None or isinstance({name}, {it}) else check.opt_inst_param({name}, "{name}", {it})'
                    elif inner_origin is Callable or inner_origin is collections.abc.Callable:
                        return f'{name} if {name} is None else check.opt_callable_param({name}, "{name}")'

            # union
            else:
                tuple_types = _coerce_type(ttype, eval_ctx)
                if tuple_types is not None:
                    tt_name = _name(tuple_types)
                    return f'{name} if isinstance({name}, {tt_name}) else check.inst_param({name}, "{name}", {tt_name})'

        # origin is some other type, assume ttype is Generic representation
        else:
            inst_type = _coerce_type(ttype, eval_ctx)
            if inst_type:
                it = _name(inst_type)
                return f'{name} if isinstance({name}, {it}) else check.inst_param({name}, "{name}", {it})'

        failed(f"Unhandled {ttype}")


def build_args_and_assignment_strs(
    fn_args: Iterable[str],
    defaults: Mapping[str, Any],
    kw_only: bool,
) -> tuple[str, str]:
    """Utility function to create the arguments to the function as well as any
    assignment calls that need to happen for default values.
    """
    args = []
    set_calls = []
    for arg in fn_args:
        if arg in defaults:
            default = defaults[arg]
            if default is None:
                args.append(f"{arg} = None")
            # dont share class instance of default empty containers
            elif default == []:
                args.append(f"{arg} = None")
                set_calls.append(f"{arg} = {arg} if {arg} is not None else []")
            elif default == {}:
                args.append(f"{arg} = None")
                set_calls.append(f"{arg} = {arg} if {arg} is not None else {'{}'}")
            # fallback to direct reference if unknown
            else:
                args.append(f"{arg} = {INJECTED_DEFAULT_VALS_LOCAL_VAR}['{arg}']")
        else:
            args.append(arg)

    args_str = ""
    if args:
        args_str = f", {'*,' if kw_only else ''} {', '.join(args)}"

    set_calls_str = ""
    if set_calls:
        set_calls_str = "\n    ".join(set_calls)

    return args_str, set_calls_str
