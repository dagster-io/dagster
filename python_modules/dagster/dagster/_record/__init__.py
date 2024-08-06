import inspect
from abc import ABC
from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Mapping,
    NamedTuple,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    overload,
)

from typing_extensions import Self, dataclass_transform

import dagster._check as check
from dagster._check import EvalContext, build_check_call_str

ImportFrom = check.ImportFrom  # re-expose for convenience
TType = TypeVar("TType", bound=Type)
TVal = TypeVar("TVal")


_RECORD_MARKER_VALUE = object()
_RECORD_MARKER_FIELD = (
    "__checkrepublic__"  # "I do want to release this as checkrepublic one day" - schrockn
)
_RECORD_ANNOTATIONS_FIELD = "__record_annotations__"
_CHECKED_NEW = "__checked_new__"
_DEFAULTS_NEW = "__defaults_new__"
_INJECTED_DEFAULT_VALS_LOCAL_VAR = "__dm_defaults__"
_NAMED_TUPLE_BASE_NEW_FIELD = "__nt_new__"
_REMAPPING_FIELD = "__field_remap__"
_ORIGINAL_CLASS_FIELD = "__original_class__"


def _namedtuple_record_transform(
    cls: TType,
    *,
    checked: bool,
    with_new: bool,
    decorator_frames: int,
    field_to_new_mapping: Optional[Mapping[str, str]],
) -> TType:
    """Transforms the input class in to one that inherits a generated NamedTuple base class
    and:
        * bans tuple methods that don't make sense for a record object
        * creates a run time checked __new__  (optional).
    """
    field_set = getattr(cls, "__annotations__", {})

    defaults = {}
    for name in field_set.keys():
        if hasattr(cls, name):
            attr_val = getattr(cls, name)
            if isinstance(attr_val, property):
                check.invariant(
                    attr_val.__isabstractmethod__,
                    f"Conflicting non-abstract @property for field {name} on record {cls.__name__}."
                    "Add the the @abstractmethod decorator to make it abstract.",
                )
            else:
                check.invariant(
                    not inspect.isfunction(attr_val),
                    f"Conflicting function for field {name} on record {cls.__name__}. "
                    "If you are trying to set a function as a default value "
                    "you will have to override __new__.",
                )
                defaults[name] = attr_val

    base = NamedTuple(f"_{cls.__name__}", field_set.items())
    nt_new = base.__new__
    if checked:
        eval_ctx = EvalContext.capture_from_frame(
            1 + decorator_frames,
            # inject default values in to the local namespace for reference in generated __new__
            add_to_local_ns={_INJECTED_DEFAULT_VALS_LOCAL_VAR: defaults},
        )
        jit_checked_new = JitCheckedNew(
            field_set,
            defaults,
            base,
            eval_ctx,
            1 if with_new else 0,
        )
        base.__new__ = jit_checked_new

    elif defaults:
        # allow arbitrary ordering of default values by generating a kwarg only __new__ impl
        eval_ctx = EvalContext(
            global_ns={},
            # inject default values in to the local namespace for reference in generated __new__
            local_ns={_INJECTED_DEFAULT_VALS_LOCAL_VAR: defaults},
            lazy_imports={},
        )
        defaults_new = eval_ctx.compile_fn(
            _build_defaults_new(field_set, defaults),
            _DEFAULTS_NEW,
        )
        base.__new__ = defaults_new

    if with_new and cls.__new__ is object.__new__:
        # verify the alignment since it impacts frame capture
        check.failed(f"Expected __new__ on {cls}, add it or switch from the _with_new decorator.")

    new_type = type(
        cls.__name__,
        (cls, base),
        {  # these will override an implementation on the class if it exists
            **{n: getattr(base, n) for n in field_set.keys()},
            "__iter__": _banned_iter,
            "__getitem__": _banned_idx,
            "__hidden_iter__": base.__iter__,
            _RECORD_MARKER_FIELD: _RECORD_MARKER_VALUE,
            _RECORD_ANNOTATIONS_FIELD: field_set,
            _NAMED_TUPLE_BASE_NEW_FIELD: nt_new,
            _REMAPPING_FIELD: field_to_new_mapping or {},
            _ORIGINAL_CLASS_FIELD: cls,
            "__bool__": _true,
            "__reduce__": _reduce,
            # functools doesn't work, so manually update_wrapper
            "__module__": cls.__module__,
            "__qualname__": cls.__qualname__,
            "__annotations__": field_set,
            "__doc__": cls.__doc__,
        },
    )

    return new_type  # type: ignore


@overload
def record(
    cls: TType,
) -> TType: ...  # Overload for using decorator with no ().


@overload
def record(
    *,
    checked: bool = True,
) -> Callable[[TType], TType]: ...  # Overload for using decorator used with args.


@dataclass_transform(
    kw_only_default=True,
    frozen_default=True,
)
def record(
    cls: Optional[TType] = None,
    *,
    checked: bool = True,
) -> Union[TType, Callable[[TType], TType]]:
    """A class decorator that will create an immutable record class based on the defined fields.

    Args:
        checked: Whether or not to generate runtime type checked construction.
    """
    if cls:
        return _namedtuple_record_transform(
            cls,
            checked=checked,
            with_new=False,
            decorator_frames=1,
            field_to_new_mapping=None,
        )
    else:
        return partial(
            _namedtuple_record_transform,
            checked=checked,
            with_new=False,
            decorator_frames=0,
            field_to_new_mapping=None,
        )


@overload
def record_custom(
    cls: TType,
) -> TType: ...  # Overload for using decorator with no ().


@overload
def record_custom(
    *,
    checked: bool = True,
    field_to_new_mapping: Optional[Mapping[str, str]] = None,
) -> Callable[[TType], TType]: ...  # Overload for using decorator used with args.


def record_custom(
    cls: Optional[TType] = None,
    *,
    checked: bool = True,
    field_to_new_mapping: Optional[Mapping[str, str]] = None,
) -> Union[TType, Callable[[TType], TType]]:
    """Variant of the record decorator to use to opt out of the dataclass_transform decorator behavior.
    This is often doesn't to be able to override __new__, so the type checker respects your constructor.

    @record_custom
    class Coerced(IHaveNew):
        name: str

        def __new__(cls, name: Optional[str] = None)
            if not name:
                name = "bob"

            return super().__new__(
                cls,
                name=name,
            )



    It would have been cool if we could do that with an argument and @overload but
    from https://peps.python.org/pep-0681/ " When applied to an overload,
    the dataclass_transform decorator still impacts all usage of the function."
    """
    if cls:
        return _namedtuple_record_transform(
            cls,
            checked=checked,
            with_new=True,
            decorator_frames=1,
            field_to_new_mapping=field_to_new_mapping,
        )
    else:
        return partial(
            _namedtuple_record_transform,
            checked=checked,
            with_new=True,
            decorator_frames=0,
            field_to_new_mapping=field_to_new_mapping,
        )


class IHaveNew:
    """Marker class to be used when overriding new in @record_custom classes to prevent
    type errors when calling super().__new__.
    """

    if TYPE_CHECKING:

        def __new__(cls, **kwargs) -> Self: ...


def is_record(obj) -> bool:
    """Whether or not this object was produced by a record decorator."""
    return getattr(obj, _RECORD_MARKER_FIELD, None) == _RECORD_MARKER_VALUE


def has_generated_new(obj) -> bool:
    return obj.__new__.__name__ in (_DEFAULTS_NEW, _CHECKED_NEW)


def get_record_annotations(obj) -> Mapping[str, Type]:
    check.invariant(is_record(obj), "Only works for @record decorated classes")
    return getattr(obj, _RECORD_ANNOTATIONS_FIELD)


def get_original_class(obj):
    check.invariant(is_record(obj), "Only works for @record decorated classes")
    return getattr(obj, _ORIGINAL_CLASS_FIELD)


def as_dict(obj) -> Mapping[str, Any]:
    """Creates a dict representation of the record based on the fields."""
    check.invariant(is_record(obj), "Only works for @record decorated classes")

    return {key: value for key, value in zip(obj._fields, obj.__hidden_iter__())}


def as_dict_for_new(obj) -> Mapping[str, Any]:
    """Creates a dict representation of the record with field_to_new_mapping applied."""
    check.invariant(is_record(obj), "Only works for @record decorated classes")

    remap = getattr(obj, _REMAPPING_FIELD)
    from_obj = {}
    for k, v in as_dict(obj).items():
        if k in remap:
            from_obj[remap[k]] = v
        else:
            from_obj[k] = v

    return from_obj


def copy(obj: TVal, **kwargs) -> TVal:
    """Create a copy of this record instance, with new values specified as key word args."""
    return obj.__class__(
        **{
            **as_dict_for_new(obj),
            **kwargs,
        }
    )


class LegacyNamedTupleMixin(ABC):
    """Mixin to ease migration by adding NamedTuple utility methods.
    Inherit when converting an existing NamedTuple that has callsites to _replace / _asdict, ie.

    @record
    def AssetSubset(LegacyNamedTupleMixin):
        asset_key: AssetKey
        value: Union[bool, PartitionsSubset]
    """

    def _replace(self, **kwargs):
        return copy(self, **kwargs)

    def _asdict(self):
        return as_dict(self)


class JitCheckedNew:
    """Object that allows us to just-in-time compile a checked __new__ implementation on first use.
    This has two benefits:
        1. Defer processing ForwardRefs until their definitions are in scope.
        2. Avoid up-front cost for unused objects.
    """

    __name__ = _CHECKED_NEW

    def __init__(
        self,
        field_set: Mapping[str, Type],
        defaults: Mapping[str, Any],
        nt_base: Type,
        eval_ctx: EvalContext,
        new_frames: int,
    ):
        self._field_set = field_set
        self._defaults = defaults
        self._nt_base = nt_base
        self._eval_ctx = eval_ctx
        self._new_frames = new_frames  # how many frames of __new__ there are

    def __call__(self, cls, *args, **kwargs):
        # update the context with callsite locals/globals to resolve
        # ForwardRefs that were unavailable at definition time.
        self._eval_ctx.update_from_frame(1 + self._new_frames)

        # ensure check is in scope
        if "check" not in self._eval_ctx.global_ns:
            self._eval_ctx.global_ns["check"] = check

        # jit that shit
        self._nt_base.__new__ = self._eval_ctx.compile_fn(
            self._build_checked_new_str(),
            _CHECKED_NEW,
        )

        return self._nt_base.__new__(cls, *args, **kwargs)

    def _build_checked_new_str(self) -> str:
        kw_args_str, set_calls_str = build_args_and_assignment_strs(self._field_set, self._defaults)
        check_calls = []
        for name, ttype in self._field_set.items():
            call_str = build_check_call_str(
                ttype=ttype,
                name=name,
                eval_ctx=self._eval_ctx,
            )
            check_calls.append(f"{name}={call_str}")

        check_call_block = ",\n        ".join(check_calls)

        lazy_imports_str = "\n    ".join(
            f"from {module} import {t}" for t, module in self._eval_ctx.lazy_imports.items()
        )

        return f"""
def __checked_new__(cls{kw_args_str}):
    {lazy_imports_str}
    {set_calls_str}
    return cls.{_NAMED_TUPLE_BASE_NEW_FIELD}(
        cls,
        {check_call_block}
    )
"""


def _build_defaults_new(
    field_set: Mapping[str, Type],
    defaults: Mapping[str, Any],
) -> str:
    """Build a __new__ implementation that handles default values."""
    kw_args_str, set_calls_str = build_args_and_assignment_strs(field_set, defaults)
    assign_str = ",\n        ".join([f"{name}={name}" for name in field_set.keys()])
    return f"""
def __defaults_new__(cls{kw_args_str}):
    {set_calls_str}
    return cls.{_NAMED_TUPLE_BASE_NEW_FIELD}(
        cls,
        {assign_str}
    )
    """


def build_args_and_assignment_strs(
    field_set: Mapping[str, Type],
    defaults: Mapping[str, Any],
) -> Tuple[str, str]:
    """Utility funciton shared between _defaults_new and _checked_new to create the arguments to
    the function as well as any assignment calls that need to happen.
    """
    kw_args = []
    set_calls = []
    for arg in field_set.keys():
        if arg in defaults:
            default = defaults[arg]
            if default is None:
                kw_args.append(f"{arg} = None")
            # dont share class instance of default empty containers
            elif default == []:
                kw_args.append(f"{arg} = None")
                set_calls.append(f"{arg} = {arg} if {arg} is not None else []")
            elif default == {}:
                kw_args.append(f"{arg} = None")
                set_calls.append(f"{arg} = {arg} if {arg} is not None else {'{}'}")
            # fallback to direct reference if unknown
            else:
                kw_args.append(f"{arg} = {_INJECTED_DEFAULT_VALS_LOCAL_VAR}['{arg}']")
        else:
            kw_args.append(arg)

    kw_args_str = ""
    if kw_args:
        kw_args_str = f", *, {', '.join(kw_args)}"

    set_calls_str = ""
    if set_calls:
        set_calls_str = "\n    ".join(set_calls)

    return kw_args_str, set_calls_str


def _banned_iter(*args, **kwargs):
    raise Exception("Iteration is not allowed on `@record`s.")


def _banned_idx(*args, **kwargs):
    raise Exception("Index access is not allowed on `@record`s.")


def _true(_):
    return True


def _from_reduce(cls, kwargs):
    return cls(**kwargs)


def _reduce(self):
    # pickle support
    return _from_reduce, (self.__class__, as_dict_for_new(self))
