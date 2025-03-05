import copy
import json
from abc import abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Generic, Optional, TypeVar

from typing_extensions import Self

from dagster_dg.component_key import ComponentKey, ObjectKey
from dagster_dg.utils import is_valid_json

if TYPE_CHECKING:
    from dagster_dg.context import DgContext


@dataclass
class RemoteComponentType:
    name: str
    namespace: str
    summary: Optional[str]
    description: Optional[str]
    component_schema: Optional[Mapping[str, Any]]  # json schema


@dataclass
class RemoteScaffoldableObject:
    name: str
    namespace: str
    scaffold_params_schema: Optional[Mapping[str, Any]]  # json schema


K = TypeVar("K", bound=ObjectKey)
V = TypeVar("V")


class RemoteObjectRegistry(Generic[K, V]):
    def __init__(self, objects: dict[K, V]):
        self._objects: dict[K, V] = copy.copy(objects)

    @classmethod
    @abstractmethod
    def from_dg_context(
        cls, dg_context: "DgContext", extra_modules: Optional[Sequence[str]] = None
    ) -> Self: ...

    @classmethod
    def empty(cls) -> Self:
        return cls({})

    def get(self, key: K) -> V:
        """Resolves a component type within the scope of a given component directory."""
        return self._objects[key]

    def has(self, key: K) -> bool:
        return key in self._objects

    def keys(self) -> Iterable[K]:
        yield from sorted(self._objects.keys(), key=lambda k: k.to_typename())

    def items(self) -> Iterable[tuple[K, V]]:
        yield from self._objects.items()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {list(self._objects.keys())}>"


class RemoteComponentRegistry(RemoteObjectRegistry[ComponentKey, RemoteComponentType]):
    @classmethod
    def from_dg_context(
        cls, dg_context: "DgContext", extra_modules: Optional[Sequence[str]] = None
    ) -> "RemoteComponentRegistry":
        return cls(
            _load_objects_from_context(
                dg_context, ComponentKey, RemoteComponentType, "component-types", extra_modules
            )
        )


class RemoteScaffoldableObjectRegistry(RemoteObjectRegistry[ObjectKey, RemoteScaffoldableObject]):
    @classmethod
    def from_dg_context(
        cls, dg_context: "DgContext", extra_modules: Optional[Sequence[str]] = None
    ) -> "RemoteScaffoldableObjectRegistry":
        return cls(
            _load_objects_from_context(
                dg_context, ObjectKey, RemoteScaffoldableObject, "component-types", extra_modules
            )
        )


def all_components_schema_from_dg_context(dg_context: "DgContext") -> Mapping[str, Any]:
    """Generate a schema for all components in the current environment, or retrieve it from the cache."""
    schema_raw = None
    if dg_context.has_cache:
        cache_key = dg_context.get_cache_key("all_components_schema")
        schema_raw = dg_context.cache.get(cache_key)

    if not schema_raw:
        schema_raw = dg_context.external_components_command(["list", "all-components-schema"])
    return json.loads(schema_raw)


# ########################
# ##### HELPERS
# ########################


def _load_objects_from_context(
    dg_context: "DgContext",
    key_type: type[K],
    value_type: type[V],
    subcommand: str,
    extra_modules: Optional[Sequence[str]] = None,
) -> dict[K, V]:
    """Fetches the set of available scaffoldable objects. The default set includes everything
    discovered under the "dagster.components" entry point group in the target environment. If
    `extra_modules` is provided, these will also be searched for component types.
    """
    if dg_context.use_dg_managed_environment:
        dg_context.ensure_uv_lock()

    if dg_context.config.cli.use_component_modules:
        component_data = _load_module_components(
            dg_context,
            dg_context.config.cli.use_component_modules,
            key_type,
            value_type,
            subcommand,
        )
    else:
        component_data = _load_entry_point_data(dg_context, key_type, value_type, subcommand)

    if extra_modules:
        component_data.update(
            _load_module_components(dg_context, extra_modules, key_type, value_type, subcommand)
        )

    return component_data


def _load_entry_point_data(
    dg_context: "DgContext", key_type: type[K], value_type: type[V], subcommand: str
) -> dict[K, V]:
    if dg_context.has_cache:
        cache_key = dg_context.get_cache_key(f"remote_object_data[{value_type.__name__}]")
        raw_registry_data = dg_context.cache.get(cache_key)
    else:
        cache_key = None
        raw_registry_data = None

    if not raw_registry_data:
        raw_registry_data = dg_context.external_components_command(["list", subcommand])
        if dg_context.has_cache and cache_key and is_valid_json(raw_registry_data):
            dg_context.cache.set(cache_key, raw_registry_data)

    return _parse_raw_registry_data(raw_registry_data, key_type, value_type)


def _load_module_components(
    dg_context: "DgContext",
    modules: Sequence[str],
    key_type: type[K],
    value_type: type[V],
    subcommand: str,
) -> dict[K, V]:
    modules_to_fetch = set(modules)
    data: dict[K, V] = {}
    if dg_context.has_cache:
        for module in modules:
            cache_key = dg_context.get_cache_key_for_module(module)
            raw_data = dg_context.cache.get(cache_key)
            if raw_data:
                data.update(_parse_raw_registry_data(raw_data, key_type, value_type))
                modules_to_fetch.remove(module)

    if modules_to_fetch:
        raw_local_component_data = dg_context.external_components_command(
            [
                "list",
                subcommand,
                "--no-entry-points",
                *modules_to_fetch,
            ]
        )
        all_fetched_components = _parse_raw_registry_data(
            raw_local_component_data, key_type, value_type
        )
        for module in modules_to_fetch:
            components = {k: v for k, v in all_fetched_components.items() if k.namespace == module}
            data.update(components)

            if dg_context.has_cache:
                cache_key = dg_context.get_cache_key_for_module(module)
                dg_context.cache.set(cache_key, _dump_raw_registry_data(components))

    return data


def _parse_raw_registry_data(
    raw_registry_data: str, key_type: type[K], value_type: type[V]
) -> dict[K, V]:
    return {
        key_type.from_typename(typename): value_type(**metadata)
        for typename, metadata in json.loads(raw_registry_data).items()
    }


def _dump_raw_registry_data(registry_data: Mapping) -> str:
    return json.dumps(
        {key.to_typename(): asdict(component) for key, component in registry_data.items()}
    )
