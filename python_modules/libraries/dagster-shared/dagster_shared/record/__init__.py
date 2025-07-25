import inspect
import os
import sys
from abc import ABC
from collections import namedtuple
from collections.abc import Iterator, Mapping
from functools import partial
from typing import TYPE_CHECKING, Any, Callable, NamedTuple, Optional, TypeVar, Union, overload

from typing_extensions import Self, dataclass_transform

import dagster_shared.check as check
from dagster_shared.check.builder import (
    INJECTED_CHECK_VAR,
    INJECTED_DEFAULT_VALS_LOCAL_VAR,
    EvalContext,
    build_args_and_assignment_strs,
    build_check_call_str,
)
from dagster_shared.check.record import RECORD_MARKER_FIELD, RECORD_MARKER_VALUE, is_record

ImportFrom = check.ImportFrom  # re-expose for convenience
TType = TypeVar("TType", bound=type)
TVal = TypeVar("TVal")


_RECORD_ANNOTATIONS_FIELD = "__record_annotations__"
_RECORD_DEFAULTS_FIELD = "__record_defaults__"
_CHECKED_NEW = "__checked_new__"
_DEFAULTS_NEW = "__defaults_new__"
_NAMED_TUPLE_BASE_NEW_FIELD = "__nt_new__"
_REMAPPING_FIELD = "__field_remap__"
_ORIGINAL_CLASS_FIELD = "__original_class__"
_KW_ONLY_FIELD = "__kw_only__"


_sample_nt = namedtuple("_canary", "x")
# use a sample to avoid direct private imports (_collections._tuplegetter)
_tuple_getter_type = type(getattr(_sample_nt, "x"))


def _get_field_set_and_defaults(
    cls: type,
    kw_only: bool,
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    field_set = getattr(cls, "__annotations__", {})
    defaults = {}

    last_defaulted_field = None
    for name in field_set.keys():
        if hasattr(cls, name):
            attr_val = getattr(cls, name)
            if isinstance(attr_val, property):
                check.invariant(
                    attr_val.__isabstractmethod__,
                    f"Conflicting non-abstract @property for field {name} on record {cls.__name__}."
                    "Add the the @abstractmethod decorator to make it abstract.",
                )
            # When doing record inheritance, filter out tuplegetters from parents.
            # This workaround only seems needed for py3.9
            elif not isinstance(attr_val, _tuple_getter_type):
                check.invariant(
                    not inspect.isfunction(attr_val),
                    f"Conflicting function for field {name} on record {cls.__name__}. "
                    "If you are trying to set a function as a default value "
                    "you will have to override __new__.",
                )
                if "pydantic" in sys.modules:
                    from pydantic.fields import FieldInfo

                    check.invariant(
                        not isinstance(attr_val, FieldInfo),
                        "pydantic.Field is not supported as a default value for @record fields."
                        " For Resolved subclasses, you may provide additional field metadata"
                        " through the Resolver: Annotated[..., Resolver.default(description=...)].",
                    )
                defaults[name] = attr_val
                last_defaulted_field = name
                continue

        # fall through here means no default set
        if last_defaulted_field and not kw_only:
            check.failed(
                "Fields without defaults cannot appear after fields with default values. "
                f"Field {name} has no default after {last_defaulted_field} with default value."
            )

    for base in cls.__bases__:
        if is_record(base):
            original_base = getattr(base, _ORIGINAL_CLASS_FIELD)
            base_kw_only = getattr(base, _KW_ONLY_FIELD)
            check.invariant(
                kw_only == base_kw_only,
                "Can not inherit from a parent @record with different kw_only setting.",
            )
            base_field_set, base_defaults = _get_field_set_and_defaults(original_base, kw_only)
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
    kw_only: bool,
) -> TType:
    """Transforms the input class in to one that inherits a generated NamedTuple base class
    and:
        * bans tuple methods that don't make sense for a record object
        * creates a run time checked __new__  (optional).
    """
    field_set, defaults = _get_field_set_and_defaults(cls, kw_only)

    base = NamedTuple(f"_{cls.__name__}", field_set.items())
    nt_new = base.__new__

    generated_new = None
    if checked:
        eval_ctx = EvalContext.capture_from_frame(
            1 + decorator_frames,
            add_to_local_ns={
                # inject default values in to the local namespace for reference in generated __new__
                INJECTED_DEFAULT_VALS_LOCAL_VAR: defaults,
                # as well as a ref to the check module
                INJECTED_CHECK_VAR: check,
            },
        )
        generated_new = JitCheckedNew(
            field_set,
            defaults,
            eval_ctx,
            new_frames=1 if with_new else 0,
            kw_only=kw_only,
        )
    elif defaults:
        # allow arbitrary ordering of default values by generating a kwarg only __new__ impl
        eval_ctx = EvalContext(
            global_ns={},
            # inject default values in to the local namespace for reference in generated __new__
            local_ns={INJECTED_DEFAULT_VALS_LOCAL_VAR: defaults},
            lazy_imports={},
        )
        generated_new = eval_ctx.compile_fn(
            _build_defaults_new(field_set, defaults, kw_only),
            _DEFAULTS_NEW,
        )

    # the default namedtuple record cannot handle subclasses that have different fields from their
    # parents if both are records
    base.__repr__ = _repr
    nt_iter = base.__iter__

    # disable iteration unless the debugger is running which uses iteration to display values
    if not os.getenv("DEBUGPY_RUNNING"):
        base.__iter__ = _banned_iter
        base.__getitem__ = _banned_idx

    # these will override an implementation on the class if it exists
    new_class_dict = {
        **{n: getattr(base, n) for n in field_set.keys()},
        "_fields": base._fields,
        "__hidden_iter__": nt_iter,
        "__hidden_replace__": base._replace,
        RECORD_MARKER_FIELD: RECORD_MARKER_VALUE,
        _RECORD_ANNOTATIONS_FIELD: field_set,
        _RECORD_DEFAULTS_FIELD: defaults,
        _NAMED_TUPLE_BASE_NEW_FIELD: nt_new,
        _REMAPPING_FIELD: field_to_new_mapping or {},
        _ORIGINAL_CLASS_FIELD: cls,
        _KW_ONLY_FIELD: kw_only,
        "__reduce__": _reduce,
        # functools doesn't work, so manually update_wrapper
        "__module__": cls.__module__,
        "__qualname__": cls.__qualname__,
        "__annotations__": field_set,
        "__doc__": cls.__doc__,
        "__get_pydantic_core_schema__": _pydantic_core_schema,
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
    kw_only: bool = True,
) -> Callable[[TType], TType]: ...  # Overload for using decorator used with args.


@dataclass_transform(
    kw_only_default=True,
    frozen_default=True,
)
def record(
    cls: Optional[TType] = None,
    *,
    checked: bool = True,
    kw_only: bool = True,
) -> Union[TType, Callable[[TType], TType]]:
    """A class decorator that will create an immutable record class based on the defined fields.

    Args:
        checked: Whether or not to generate runtime type checked construction (default True).
        kw_only: Whether or not the generated __new__ is kwargs only (default True).

    Example:
        @record
        class Person:
            name: str
            age: int

        # Create instance
        person = Person(name="Alice", age=30)

        # Create modified copy using replace()
        older_person = replace(person, age=31)

        # Add items to lists using replace()
        @record
        class TaskList:
            items: list[str]

        tasks = TaskList(items=["task1"])
        updated_tasks = replace(tasks, items=[*tasks.items, "task2"])
    """
    if cls:
        return _namedtuple_record_transform(
            cls,
            checked=checked,
            with_new=False,
            decorator_frames=1,
            field_to_new_mapping=None,
            kw_only=kw_only,
        )
    else:
        return partial(
            _namedtuple_record_transform,
            checked=checked,
            with_new=False,
            decorator_frames=0,
            field_to_new_mapping=None,
            kw_only=kw_only,
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
    """Variant of the record decorator to use when overriding __new__.

    Example:
        @record_custom
        class MyRecord(IHaveNew):
            name: str
            value: int

            def __new__(cls, name: str, value: int = 42):
                # Custom logic here
                if not name:
                    name = "default"
                return super().__new__(
                    cls,
                    name=name,
                    value=value,
                )

    Important requirements:
    - Must inherit from IHaveNew
    - Must define a custom __new__ method
    - Must call super().__new__(cls, **kwargs) with keyword arguments
    - Keyword arguments must match the field names exactly
    - Cannot be used with @record inheritance

    This approach is useful when you need custom validation, default value logic,
    or type coercion in the constructor that can't be handled with simple defaults.

    It would have been cool if we could do that with an argument and @overload but
    from https://peps.python.org/pep-0681/ "When applied to an overload,
    the dataclass_transform decorator still impacts all usage of the function."
    """
    if cls:
        return _namedtuple_record_transform(
            cls,
            checked=checked,
            with_new=True,
            decorator_frames=1,
            field_to_new_mapping=field_to_new_mapping,
            kw_only=True,
        )
    else:
        return partial(
            _namedtuple_record_transform,
            checked=checked,
            with_new=True,
            decorator_frames=0,
            field_to_new_mapping=field_to_new_mapping,
            kw_only=True,
        )


class IHaveNew:
    """Marker class to be used when overriding new in @record_custom classes to prevent
    type errors when calling super().__new__.
    """

    if TYPE_CHECKING:

        def __new__(cls, **kwargs) -> Self: ...

        # let type checker know these objects are sortable (by way of being a namedtuple)
        def __lt__(self, other) -> bool: ...


def has_generated_new(obj) -> bool:
    return obj.__new__.__name__ in (_DEFAULTS_NEW, _CHECKED_NEW)


def get_record_annotations(obj) -> Mapping[str, type]:
    check.invariant(is_record(obj), "Only works for @record decorated classes")
    return getattr(obj, _RECORD_ANNOTATIONS_FIELD)


def get_record_defaults(obj) -> Mapping[str, Any]:
    check.invariant(is_record(obj), "Only works for @record decorated classes")
    return getattr(obj, _RECORD_DEFAULTS_FIELD)


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

    Example:
        @record
        class Config:
            timeout: int
            retries: int

        config = Config(timeout=30, retries=3)

        # Update single field
        faster_config = replace(config, timeout=10)

        # Update multiple fields
        production_config = replace(config, timeout=60, retries=5)

        # Add items to lists (use spread operator to avoid mutation)
        @record
        class Results:
            errors: list[str]
            warnings: list[str]

        results = Results(errors=[], warnings=["deprecated API"])

        # Add new error
        updated_results = replace(results, errors=[*results.errors, "network timeout"])

        # Add multiple items
        final_results = replace(
            updated_results,
            errors=[*updated_results.errors, "connection failed"],
            warnings=[*updated_results.warnings, "slow query"]
        )
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

    def _replace(self, **kwargs) -> Self:
        return replace(self, **kwargs)

    def _asdict(self) -> Mapping[str, Any]:
        return as_dict(self)

    def __iter__(self) -> Iterator:
        return tuple.__iter__(self)  # type: ignore


class JitCheckedNew:
    """Object that allows us to just-in-time compile a checked __new__ implementation on first use.
    This has two benefits:
        1. Defer processing ForwardRefs until their definitions are in scope.
        2. Avoid up-front cost for unused objects.
    """

    __name__ = _CHECKED_NEW

    def __init__(
        self,
        field_set: Mapping[str, type],
        defaults: Mapping[str, Any],
        eval_ctx: EvalContext,
        new_frames: int,
        kw_only: bool,
    ):
        self._field_set = field_set
        self._defaults = defaults
        self._eval_ctx = eval_ctx
        self._new_frames = new_frames  # how many frames of __new__ there are
        self._compiled = False
        self._kw_only = kw_only

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
        args_str, set_calls_str = build_args_and_assignment_strs(
            self._field_set.keys(),
            self._defaults,
            self._kw_only,
        )
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
def __checked_new__(cls{args_str}):
    {lazy_imports_str}
    {set_calls_str}
    return cls.{_NAMED_TUPLE_BASE_NEW_FIELD}(
        cls,
        {check_call_block}
    )
"""
        return checked_new_str


def _build_defaults_new(
    field_set: Mapping[str, type],
    defaults: Mapping[str, Any],
    kw_only: bool,
) -> str:
    """Build a __new__ implementation that handles default values."""
    kw_args_str, set_calls_str = build_args_and_assignment_strs(
        field_set,
        defaults,
        kw_only,
    )
    assign_str = ",\n        ".join([f"{name}={name}" for name in field_set.keys()])
    return f"""
def __defaults_new__(cls{kw_args_str}):
    {set_calls_str}
    return cls.{_NAMED_TUPLE_BASE_NEW_FIELD}(
        cls,
        {assign_str}
    )
    """


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


@classmethod
def _pydantic_core_schema(cls, source: Any, handler):
    """Forces pydantic_core to treat records as normal types instead of namedtuples. In particular,
    pydantic assumes that all namedtuples can be constructed with posargs, while records are kw-only.
    """
    from pydantic_core import core_schema

    return core_schema.is_instance_schema(cls)
