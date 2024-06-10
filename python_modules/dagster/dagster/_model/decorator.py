from abc import ABC
from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Mapping,
    NamedTuple,
    Optional,
    Type,
    TypeVar,
    Union,
    overload,
)

from typing_extensions import dataclass_transform

import dagster._check as check
from dagster._check import EvalContext, build_check_call_str

TType = TypeVar("TType", bound=Type)
TVal = TypeVar("TVal")


_MODEL_MARKER_VALUE = object()
_MODEL_MARKER_FIELD = (
    "__checkrepublic__"  # "I do want to release this as checkrepublic one day" - schrockn
)
_GENERATED_NEW = "__checked_new__"


def _namedtuple_model_transform(
    cls: TType,
    *,
    checked: bool,
    with_new: bool,
    decorator_frames: int,
) -> TType:
    """Transforms the input class in to one that inherits a generated NamedTuple base class
    and:
        * bans tuple methods that don't make sense for a model object
        * creates a run time checked __new__  (optional).
    """
    base = NamedTuple(f"_{cls.__name__}", cls.__annotations__.items())
    nt_new = base.__new__
    if checked:
        jit_checked_new = JitCheckedNew(
            cls.__annotations__,
            EvalContext.capture_from_frame(1 + decorator_frames),
            1 if with_new else 0,
            base,
        )
        base.__new__ = jit_checked_new  # type: ignore

    if with_new and cls.__new__ is object.__new__:
        # verify the alignment since it impacts frame capture
        check.failed(f"Expected __new__ on {cls}, add it or switch from the _with_new decorator.")

    new_type = type(
        cls.__name__,
        (cls, base),
        {  # these will override an implementation on the class if it exists
            "__iter__": _banned_iter,
            "__getitem__": _banned_idx,
            "__hidden_iter__": base.__iter__,
            _MODEL_MARKER_FIELD: _MODEL_MARKER_VALUE,
            "__annotations__": cls.__annotations__,
            "__nt_new__": nt_new,
        },
    )

    return new_type  # type: ignore


@overload
def dagster_model(
    cls: TType,
) -> TType: ...  # Overload for using decorator with no ().


@overload
def dagster_model(
    *,
    checked: bool = True,
) -> Callable[[TType], TType]: ...  # Overload for using decorator used with args.


@dataclass_transform(
    kw_only_default=True,
    frozen_default=True,
)
def dagster_model(
    cls: Optional[TType] = None,
    *,
    checked: bool = True,
) -> Union[TType, Callable[[TType], TType]]:
    """A class decorator that will create an immutable model class based on the defined fields.

    Args:
        checked: Whether or not to generate runtime type checked construction.
        enable_cached_method: Whether or not to support object instance level caching using @cached_method.
        serdes: whitelist this class for serdes, with the defined options if SerdesOptions used.
    """
    if cls:
        return _namedtuple_model_transform(
            cls,
            checked=checked,
            with_new=False,
            decorator_frames=1,
        )
    else:
        return partial(
            _namedtuple_model_transform,
            checked=checked,
            with_new=False,
            decorator_frames=0,
        )


@overload
def dagster_model_custom(
    cls: TType,
) -> TType: ...  # Overload for using decorator with no ().


@overload
def dagster_model_custom(
    *,
    checked: bool = True,
) -> Callable[[TType], TType]: ...  # Overload for using decorator used with args.


def dagster_model_custom(
    cls: Optional[TType] = None,
    *,
    checked: bool = True,
) -> Union[TType, Callable[[TType], TType]]:
    """Variant of the dagster_model decorator to use to opt out of the dataclass_transform decorator behavior.
    This is often doesn't to be able to override __new__, so the type checker respects your constructor.

    @dagster_model_custom
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
        return _namedtuple_model_transform(
            cls,
            checked=checked,
            with_new=True,
            decorator_frames=1,
        )
    else:
        return partial(
            _namedtuple_model_transform,
            checked=checked,
            with_new=True,
            decorator_frames=0,
        )


class IHaveNew:
    """Marker class to be used when overriding new in @dagster_model_custom classes to prevent
    type errors when calling super().__new__.
    """

    if TYPE_CHECKING:

        def __new__(cls, **kwargs): ...


def is_dagster_model(obj) -> bool:
    """Whether or not this object was produced by a dagster_model decorator."""
    return getattr(obj, _MODEL_MARKER_FIELD, None) == _MODEL_MARKER_VALUE


def has_generated_new(obj) -> bool:
    return obj.__new__.__name__ == _GENERATED_NEW


def as_dict(obj) -> Mapping[str, Any]:
    """Creates a dict representation of a model."""
    if not is_dagster_model(obj):
        raise Exception("Only works for @dagster_model decorated classes")

    return {key: value for key, value in zip(obj._fields, obj.__hidden_iter__())}


def copy(obj: TVal, **kwargs) -> TVal:
    """Create a copy of this dagster_model instance, with new values specified as key word args."""
    return obj.__class__(
        **{
            **as_dict(obj),
            **kwargs,
        }
    )


class LegacyNamedTupleMixin(ABC):
    """Mixin to ease migration by adding NamedTuple utility methods.
    Inherit when converting an existing NamedTuple that has callsites to _replace / _asdict, ie.

    @dagster_model
    def AssetSubset(LegacyNamedTupleMixin):
        asset_key: AssetKey
        value: Union[bool, PartitionsSubset]
    """

    def _replace(self, **kwargs):
        return copy(self, **kwargs)

    def _asdict(self):
        return as_dict(self)


class JitCheckedNew:
    """Object that allows us to just-in-time compile a __checked_new__ implementation on first use.
    This has two benefits:
        1. Defer processing ForwardRefs until their definitions are in scope.
        2. Avoid up-front cost for unused objects.
    """

    __name__ = _GENERATED_NEW

    def __init__(
        self,
        field_set: dict,
        eval_ctx: EvalContext,
        new_frames: int,
        nt_base: Type,
    ):
        self._field_set = field_set
        self._eval_ctx = eval_ctx
        self._new_frames = new_frames  # how many frames of __new__ there are
        self._nt_base = nt_base

    def __call__(self, cls, **kwargs):
        # update the context with callsite locals/globals to resolve
        # ForwardRefs that were unavailable at definition time.
        self._eval_ctx.update_from_frame(1 + self._new_frames)

        # ensure check is in scope
        if "check" not in self._eval_ctx.global_ns:
            self._eval_ctx.global_ns["check"] = check

        # jit that shit
        self._nt_base.__new__ = self._eval_ctx.compile_fn(
            self._build_checked_new_str(),
            _GENERATED_NEW,
        )

        return self._nt_base.__new__(cls, **kwargs)

    def _build_checked_new_str(self) -> str:
        kw_args = ", ".join(self._field_set.keys())
        check_calls = []
        for name, ttype in self._field_set.items():
            call_str = build_check_call_str(
                ttype=ttype,
                name=name,
                eval_ctx=self._eval_ctx,
            )
            check_calls.append(f"{name}={call_str}")

        check_call_block = "        ,\n".join(check_calls)
        return f"""
def __checked_new__(cls, {kw_args}):
    return cls.__nt_new__(
        cls,{check_call_block}
    )
"""


def _banned_iter(*args, **kwargs):
    raise Exception("Iteration is not allowed on `@dagster_model`s.")


def _banned_idx(*args, **kwargs):
    raise Exception("Index access is not allowed on `@dagster_model`s.")
