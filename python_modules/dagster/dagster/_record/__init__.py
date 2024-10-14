import inspect
import os
from abc import ABC
from collections import namedtuple
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


_sample_nt = namedtuple("_canary", "x")
# use a sample to avoid direct private imports (_collections._tuplegetter)
_tuple_getter_type = type(getattr(_sample_nt, "x"))


def _get_field_set_and_defaults(
    cls: Type,
) -> Tuple[Mapping[str, Any], Mapping[str, Any]]:
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
            elif isinstance(attr_val, _tuple_getter_type):
                # When doing record inheritance, filter out tuplegetters from parents.
                # This workaround only seems needed for py3.8
                continue
            else:
                check.invariant(
                    not inspect.isfunction(attr_val),
                    f"Conflicting function for field {name} on record {cls.__name__}. "
                    "If you are trying to set a function as a default value "
                    "you will have to override __new__.",
                )
                defaults[name] = attr_val

    for base in cls.__bases__:
        if is_record(base):
            original_base = getattr(base, _ORIGINAL_CLASS_FIELD)
            base_field_set, base_defaults = _get_field_set_and_defaults(original_base)
            field_set = {**base_field_set, **field_set}
            defaults = {**base_defaults, **defaults}

    return field_set, defaults


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
    field_set, defaults = _get_field_set_and_defaults(cls)

    base = NamedTuple(f"_{cls.__name__}", field_set.items())
    nt_new = base.__new__

    generated_new = None
    if checked:
        eval_ctx = EvalContext.capture_from_frame(
            1 + decorator_frames,
            # inject default values in to the local namespace for reference in generated __new__
            add_to_local_ns={_INJECTED_DEFAULT_VALS_LOCAL_VAR: defaults},
        )
        generated_new = JitCheckedNew(
            field_set,
            defaults,
            eval_ctx,
            1 if with_new else 0,
        )
    elif defaults:
        # allow arbitrary ordering of default values by generating a kwarg only __new__ impl
        eval_ctx = EvalContext(
            global_ns={},
            # inject default values in to the local namespace for reference in generated __new__
            local_ns={_INJECTED_DEFAULT_VALS_LOCAL_VAR: defaults},
            lazy_imports={},
        )
        generated_new = eval_ctx.compile_fn(
            _build_defaults_new(field_set, defaults),
            _DEFAULTS_NEW,
        )

    # the default namedtuple record cannot handle subclasses that have different fields from their
    # parents if both are records
    base.__repr__ = _repr

    # these will override an implementation on the class if it exists
    new_class_dict = {
        **{n: getattr(base, n) for n in field_set.keys()},
        "_fields": base._fields,
        "__iter__": _banned_iter,
        "__getitem__": _banned_idx,
        "__hidden_iter__": base.__iter__,
        "__hidden_replace__": base._replace,
        _RECORD_MARKER_FIELD: _RECORD_MARKER_VALUE,
        _RECORD_ANNOTATIONS_FIELD: field_set,
        _NAMED_TUPLE_BASE_NEW_FIELD: nt_new,
        _REMAPPING_FIELD: field_to_new_mapping or {},
        _ORIGINAL_CLASS_FIELD: cls,
        "__reduce__": _reduce,
        # functools doesn't work, so manually update_wrapper
        "__module__": cls.__module__,
        "__qualname__": cls.__qualname__,
        "__annotations__": field_set,
        "__doc__": cls.__doc__,
    }

    # Due to MRO issues, we can not support both @record_custom __new__ and record inheritance
    # so enforce these rules and place the generated new in the appropriate place in the class hierarchy.
    if with_new:
        if not _defines_own_new(cls):
            # verify the alignment since it impacts frame capture
            check.failed(
                f"Expected __new__ on {cls.__name__}, add it or switch from the @record_custom decorator to @record."
            )
        if is_record(cls):
            parent = next(c for c in cls.__mro__ if is_record(c))
            check.failed(
                f"@record_custom can not be used with @record inheritance. {cls.__name__} is a child of @record {parent.__name__}."
            )

        # For records with custom new, put the generated new on the NT base class
        if generated_new:
            base.__new__ = generated_new

    elif generated_new:
        if _defines_own_new(cls):
            check.failed(
                f"Found a custom __new__ on @record {cls}, use @record_custom with IHaveNew instead."
            )
        for c in cls.__mro__:
            if c is cls:
                continue

            if is_record(c) and _defines_own_new(c):
                check.failed(
                    "@record can not inherit from @record_custom. "
                    f"@record {cls.__name__} inherits from @record_custom {c.__name__}"
                )

        # For regular @records, which may inherit from other records, put new on the generated class to avoid
        # MRO resolving to the wrong NT base
        new_class_dict["__new__"] = generated_new
        new_class_dict["_make"] = base._make

    # make it so instances of records with no fields still evaluate to true
    if len(field_set) < 1:
        new_class_dict["__bool__"] = _true

    new_type = type(
        cls.__name__,
        (cls, base),
        new_class_dict,
    )

    # setting this in the dict above does not work for some reason,
    # so set it directly after instantiation
    if hasattr(cls, "__parameters__"):
        setattr(new_type, "__parameters__", cls.__parameters__)

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

        # let type checker know these objects are sortable (by way of being a namedtuple)
        def __lt__(self, other) -> bool: ...


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


def copy(record: TVal, **kwargs) -> TVal:
    """Create a new instance of this record type using its constructor with
    the original records values overrode with new values specified as key args.
    """
    return record.__class__(
        **{
            **as_dict_for_new(record),
            **kwargs,
        }
    )


def replace(obj: TVal, **kwargs) -> TVal:
    """Create a new instance of this record type using the record constructor directly,
    (bypassing any custom __new__ impl) with the original records values overrode with
    new values specified by keyword args.

    This emulates the behavior of namedtuple _replace.
    """
    check.invariant(is_record(obj))
    cls = obj.__class__

    # if we have runtime type checking, go through that to vet new field values
    if hasattr(cls, _CHECKED_NEW):
        target = _CHECKED_NEW
    else:
        target = _NAMED_TUPLE_BASE_NEW_FIELD

    return getattr(cls, target)(
        obj.__class__,
        **{**as_dict(obj), **kwargs},
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
        return replace(self, **kwargs)

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
        eval_ctx: EvalContext,
        new_frames: int,
    ):
        self._field_set = field_set
        self._defaults = defaults
        self._eval_ctx = eval_ctx
        self._new_frames = new_frames  # how many frames of __new__ there are
        self._compiled = False

    def __call__(self, cls, *args, **kwargs):
        if _do_defensive_checks():
            # this condition can happen during races in threaded envs so only
            # invariant when opted-in
            check.invariant(
                self._compiled is False,
                "failed to set compiled __new__ appropriately",
            )

        # update the context with callsite locals/globals to resolve
        # ForwardRefs that were unavailable at definition time.
        self._eval_ctx.update_from_frame(1 + self._new_frames)

        # ensure check is in scope
        if "check" not in self._eval_ctx.global_ns:
            self._eval_ctx.global_ns["check"] = check

        # we are double-memoizing this to handle some confusing mro issues
        # in which the _nt_base's __new__ method is not on the critical
        # path, causing this to get invoked multiple times
        compiled_fn = self._eval_ctx.compile_fn(
            self._build_checked_new_str(),
            _CHECKED_NEW,
        )
        self._compiled = True

        # replace this holder object with the compiled fn by finding where it was in the hierarchy
        for c in cls.__mro__:
            if c.__new__ is self:
                c.__new__ = compiled_fn

        return compiled_fn(cls, *args, **kwargs)

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

        checked_new_str = f"""
def __checked_new__(cls{kw_args_str}):
    {lazy_imports_str}
    {set_calls_str}
    return cls.{_NAMED_TUPLE_BASE_NEW_FIELD}(
        cls,
        {check_call_block}
    )
"""
        return checked_new_str


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


def _repr(self) -> str:
    # the __repr__ method generated for namedtuples cannot handle subclasses that have different
    # sets of fields
    field_set = getattr(self, _RECORD_ANNOTATIONS_FIELD)
    values = [f"{field_name}={getattr(self, field_name)!r}" for field_name in field_set]
    return f"{self.__class__.__name__}({', '.join(values)})"


def _defines_own_new(cls) -> bool:
    qualname = getattr(cls.__new__, "__qualname__", None)
    if not qualname:
        return False

    qualname_parts = cls.__new__.__qualname__.split(".")
    if len(qualname_parts) < 2:
        return False

    return qualname_parts[-2] == cls.__name__


def _do_defensive_checks():
    return bool(os.getenv("DAGSTER_RECORD_DEFENSIVE_CHECKS"))
