import sys
from abc import abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generic,
    Mapping,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
)

if sys.version_info >= (3, 9):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

import polars as pl
from dagster import InputContext, OutputContext

if TYPE_CHECKING:
    from upath import UPath


T = TypeVar("T")


# dump_to_path signature
F_D: TypeAlias = Callable[[OutputContext, T, "UPath"], None]

# load_from_path signature
F_L: TypeAlias = Callable[["UPath", InputContext], T]


class BaseTypeRouter(Generic[T]):
    """Specifies how to apply a given dump/load operation to a given type annotation.
    This base class trivially calls the dump/load functions if the type matches the most simple cases.
    """

    def __init__(self, context: Union[InputContext, OutputContext], typing_type: Any):
        self.context = context
        self.typing_type = typing_type

    @staticmethod
    @abstractmethod
    def match(context: Union[InputContext, OutputContext], typing_type: Any) -> bool:
        raise NotImplementedError

    @property
    @abstractmethod
    def is_base_type(self) -> bool:
        raise NotImplementedError

    @property
    @abstractmethod
    def inner_type(self) -> Any:
        raise NotImplementedError

    @property
    def parent_type_router(self) -> "TypeRouter":
        return resolve_type_router(self.context, self.inner_type)

    def dump(self, obj: T, path: "UPath", dump_fn: F_D) -> None:
        if self.is_base_type:
            dump_fn(cast(OutputContext, self.context), obj, path)
        else:
            self.parent_type_router.dump(obj, path, dump_fn)

    def load(self, path: "UPath", load_fn: F_L) -> T:
        if self.is_base_type:
            return load_fn(path, cast(InputContext, self.context))
        else:
            return self.parent_type_router.load(path, load_fn)


class TypeRouter(BaseTypeRouter, Generic[T]):
    """Handles default types."""

    @staticmethod
    def match(context: Union[InputContext, OutputContext], typing_type: Any) -> bool:
        return typing_type in [
            Any,
            type(None),
            None,
        ]

    @property
    def is_base_type(self) -> bool:
        return True


class OptionalTypeRouter(BaseTypeRouter, Generic[T]):
    """Handles Optional type annotations with a noop if the object is None or missing in storage."""

    @staticmethod
    def match(context: Union[InputContext, OutputContext], typing_type: Any) -> bool:
        return get_origin(typing_type) == Union and type(None) in get_args(typing_type)

    @property
    def is_base_type(self) -> bool:
        return False

    @property
    def inner_type(self) -> Any:
        return get_args(self.typing_type)[0]

    def dump(self, obj: T, path: "UPath", dump_fn: F_D) -> None:
        if obj is None:
            self.context.log.warning(f"Skipping saving optional output at {path} as it is None")
            return
        else:
            self.parent_type_router.dump(obj, path, dump_fn)

    def load(self, path: "UPath", load_fn: F_L) -> T:
        if not path.exists():
            self.context.log.warning(f"Skipping loading optional input at {path} as it is missing")
            return None  # type: ignore
        else:
            return self.parent_type_router.load(path, load_fn)


class DictTypeRouter(BaseTypeRouter, Generic[T]):
    """Handles loading partitions as dictionaries of DataFrames."""

    @staticmethod
    def match(context: Union[InputContext, OutputContext], typing_type: Any) -> bool:
        return get_origin(typing_type) in (dict, Dict, Mapping)

    @property
    def is_base_type(self) -> bool:
        return False

    @property
    def inner_type(self) -> Any:
        return get_args(self.typing_type)[1]


class PolarsTypeRouter(BaseTypeRouter, Generic[T]):
    """Handles Polars DataFrames."""

    @staticmethod
    def match(context: Union[InputContext, OutputContext], typing_type: Any) -> bool:
        return typing_type in [
            pl.DataFrame,
            pl.LazyFrame,
        ]

    @property
    def is_base_type(self) -> bool:
        return True


TYPE_ROUTERS = [TypeRouter, OptionalTypeRouter, DictTypeRouter, PolarsTypeRouter]


def resolve_type_router(
    context: Union[InputContext, OutputContext], type_to_resolve: Any
) -> TypeRouter:
    """Finds the first matching TypeRouter for the given type."""
    # try each router class in order of increasing complexity
    for router_class in TYPE_ROUTERS:
        if router_class.match(context, type_to_resolve):
            return router_class(context, type_to_resolve)

    raise RuntimeError(f"Could not resolve type router for {type_to_resolve}")
