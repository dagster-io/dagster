import sys
from abc import abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generic,
    Mapping,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
)

if sys.version_info >= (3, 9):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

import polars as pl
from dagster import InputContext, OutputContext

try:
    import pandera

    PANDERA_INSTALLED = True
except ImportError:
    PANDERA_INSTALLED = False


if TYPE_CHECKING:
    from upath import UPath


T = TypeVar("T")


# dump_to_path signature
F_D: TypeAlias = Callable[[OutputContext, T, "UPath"], None]

# load_from_path signature
F_L: TypeAlias = Callable[["UPath", InputContext], T]


class BaseTypeRouter(Generic[T]):
    """Specifies how to apply a given dump/load operation to a given type annotation."""

    def __init__(self, context: Union[InputContext, OutputContext], typing_type: Any):
        self.context = context
        self.typing_type = typing_type

    @abstractmethod
    def match(self) -> bool:
        raise NotImplementedError

    @property
    @abstractmethod
    def is_root_type(self) -> bool:
        raise NotImplementedError

    @property
    @abstractmethod
    def parent_type(self) -> Any:
        raise NotImplementedError

    @property
    def parent_type_router(self) -> "TypeRouter":
        return resolve_type_router(self.context, self.parent_type)

    @property
    def is_eager(self) -> bool:
        if self.is_root_type:
            return self.typing_type in [Any, type(None), None] or issubclass(
                self.typing_type, pl.DataFrame
            )
        else:
            return self.parent_type_router.is_eager

    @property
    def is_lazy(self) -> bool:
        if self.is_root_type:
            return issubclass(self.typing_type, pl.LazyFrame)
        else:
            return self.parent_type_router.is_lazy

    def dump(self, obj: T, path: "UPath", dump_fn: F_D) -> None:
        if self.is_root_type:
            dump_fn(self.context, obj, path)
        else:
            self.parent_type_router.dump(obj, path, dump_fn)

    def load(self, path: "UPath", load_fn: F_L) -> T:
        if self.is_root_type:
            return load_fn(path, self.context)
        else:
            return self.parent_type_router.load(path, load_fn)


class TypeRouter(BaseTypeRouter, Generic[T]):
    """Specifies how to apply a given dump/load operation to a given type annotation.
    This base class trivially calls the dump/load functions if the type matches the most simple cases.
    """

    def match(self) -> bool:
        return self.typing_type in [
            pl.DataFrame,
            pl.LazyFrame,
            Any,
            type(None),
            None,
        ]

    @property
    def is_root_type(self) -> bool:
        return True


class OptionalTypeRouter(BaseTypeRouter, Generic[T]):
    """Handles Optional type annotations with a noop if the object is None or missing in storage."""

    def match(self) -> bool:
        return get_origin(self.typing_type) == Union and type(None) in get_args(self.typing_type)

    @property
    def is_root_type(self) -> bool:
        return False

    @property
    def parent_type(self) -> Any:
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
            return None
        else:
            return self.parent_type_router.load(path, load_fn)


class DictTypeRouter(BaseTypeRouter, Generic[T]):
    """Handles loading partitions as dictionaries of DataFrames."""

    def match(self) -> bool:
        return get_origin(self.typing_type) in (dict, Dict, Mapping)

    @property
    def is_root_type(self) -> bool:
        return False

    @property
    def parent_type(self) -> Any:
        return get_args(self.typing_type)[1]


class PanderaTypeRouter(BaseTypeRouter, Generic[T]):
    """Handles loading Pandera DataFrames."""

    def match(self) -> bool:
        raise NotImplementedError("Generic types are not supported by Dagster type system. See https://github.com/dagster-io/dagster/issues/22694")

        try:
            import pandera
            import pandera.typing.polars

            return get_origin(self.typing_type) in [
                pandera.typing.polars.LazyFrame,
                pandera.typing.polars.DataFrame,
            ] and issubclass(get_args(self.typing_type)[0], pandera.DataFrameModel)
        except ImportError:
            return False

    @property
    def is_root_type(self) -> bool:
        return True

    @property
    def pandera_schema(self) -> Type[pandera.DataFrameModel]:
        return get_args(self.typing_type)[0]

    def dump(self, obj: T, path: "UPath", dump_fn: F_D) -> None:
        obj = self.pandera_schema.to_schema().validate(obj)
        router = resolve_type_router(self.context, self.parent_type)
        router.dump(obj, path, dump_fn)

    def load(self, path: "UPath", load_fn: F_L) -> T:
        router = resolve_type_router(self.context, self.parent_type)
        obj = router.load(path, load_fn)
        return self.pandera_schema.to_schema().validate(obj)


TYPE_ROUTERS = [
    TypeRouter,
    OptionalTypeRouter,
    DictTypeRouter,
]

if PANDERA_INSTALLED:
    TYPE_ROUTERS.insert(0, PanderaTypeRouter)  # make sure to add before the base TypeRouter


def resolve_type_router(
    context: Union[InputContext, OutputContext], type_to_resolve: Any
) -> TypeRouter:
    """Finds the first matching TypeRouter for the given type."""
    # try each router class in order of increasing complexity
    for router_class in TYPE_ROUTERS:
        router = router_class(context, type_to_resolve)

        if router.match():
            return router

    raise RuntimeError(f"Could not resolve type router for {type_to_resolve}")
