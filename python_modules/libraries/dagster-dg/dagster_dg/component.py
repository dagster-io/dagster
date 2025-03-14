import copy
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Optional

from dagster_dg.component_key import ComponentKey
from dagster_dg.utils import is_valid_json

if TYPE_CHECKING:
    from dagster_dg.context import DgContext


@dataclass
class RemoteComponentType:
    name: str
    namespace: str
    summary: Optional[str]
    description: Optional[str]
    scaffold_params_schema: Optional[Mapping[str, Any]]  # json schema
    component_schema: Optional[Mapping[str, Any]]  # json schema


class RemoteComponentRegistry:
    @staticmethod
    def from_dg_context(
        dg_context: "DgContext", extra_modules: Optional[Sequence[str]] = None
    ) -> "RemoteComponentRegistry":
        """Fetches the set of available component types. The default set includes everything
        discovered under the "dagster_dg.library" entry point group in the target environment. If
        `extra_modules` is provided, these will also be searched for component types.
        """
        if dg_context.use_dg_managed_environment:
            dg_context.ensure_uv_lock()

        if dg_context.config.cli.use_component_modules:
            component_data = _load_module_components(
                dg_context, dg_context.config.cli.use_component_modules
            )
        else:
            component_data = _load_entry_point_components(dg_context)

        if extra_modules:
            component_data.update(_load_module_components(dg_context, extra_modules))

        return RemoteComponentRegistry(component_data)

    def __init__(self, components: dict[ComponentKey, RemoteComponentType]):
        self._components: dict[ComponentKey, RemoteComponentType] = copy.copy(components)

    @staticmethod
    def empty() -> "RemoteComponentRegistry":
        return RemoteComponentRegistry({})

    def get(self, key: ComponentKey) -> RemoteComponentType:
        """Resolves a component type within the scope of a given component directory."""
        return self._components[key]

    def has(self, key: ComponentKey) -> bool:
        return key in self._components

    def keys(self) -> Iterable[ComponentKey]:
        yield from sorted(self._components.keys(), key=lambda k: k.to_typename())

    def items(self) -> Iterable[tuple[ComponentKey, RemoteComponentType]]:
        yield from self._components.items()

    def __repr__(self) -> str:
        return f"<RemoteComponentRegistry {list(self._components.keys())}>"


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


def _load_entry_point_components(
    dg_context: "DgContext",
) -> dict[ComponentKey, RemoteComponentType]:
    if dg_context.has_cache:
        cache_key = dg_context.get_cache_key("component_registry_data")
        raw_registry_data = dg_context.cache.get(cache_key)
    else:
        cache_key = None
        raw_registry_data = None

    if not raw_registry_data:
        raw_registry_data = dg_context.external_components_command(["list", "component-types"])
        if dg_context.has_cache and cache_key and is_valid_json(raw_registry_data):
            dg_context.cache.set(cache_key, raw_registry_data)

    return _parse_raw_registry_data(raw_registry_data)


def _load_module_components(
    dg_context: "DgContext", modules: Sequence[str]
) -> dict[ComponentKey, RemoteComponentType]:
    modules_to_fetch = set(modules)
    data: dict[ComponentKey, RemoteComponentType] = {}
    if dg_context.has_cache:
        for module in modules:
            cache_key = dg_context.get_cache_key_for_module(module)
            raw_data = dg_context.cache.get(cache_key)
            if raw_data:
                data.update(_parse_raw_registry_data(raw_data))
                modules_to_fetch.remove(module)

    if modules_to_fetch:
        raw_local_component_data = dg_context.external_components_command(
            [
                "list",
                "component-types",
                "--no-entry-points",
                *modules_to_fetch,
            ]
        )
        all_fetched_components = _parse_raw_registry_data(raw_local_component_data)
        for module in modules_to_fetch:
            components = {k: v for k, v in all_fetched_components.items() if k.namespace == module}
            data.update(components)

            if dg_context.has_cache:
                cache_key = dg_context.get_cache_key_for_module(module)
                dg_context.cache.set(cache_key, _dump_raw_registry_data(components))

    return data


def _parse_raw_registry_data(
    raw_registry_data: str,
) -> dict[ComponentKey, RemoteComponentType]:
    return {
        ComponentKey.from_typename(typename): RemoteComponentType(**metadata)
        for typename, metadata in json.loads(raw_registry_data).items()
    }


def _dump_raw_registry_data(
    registry_data: Mapping[ComponentKey, RemoteComponentType],
) -> str:
    return json.dumps(
        {key.to_typename(): asdict(component) for key, component in registry_data.items()}
    )
