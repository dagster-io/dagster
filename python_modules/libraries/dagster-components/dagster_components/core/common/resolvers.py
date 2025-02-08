from collections.abc import Mapping
from typing import Any, Optional

from dagster._core.definitions.asset_dep import AssetDep
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec

from dagster_components.core.common.schema import (
    AssetAttributesSchema,
    AssetDepSchema,
    AssetSpecSchema,
)
from dagster_components.core.resolution_engine.context import ResolutionContext
from dagster_components.core.resolution_engine.resolver import Resolver, resolver


def _resolve_asset_key(key: str, context: ResolutionContext) -> AssetKey:
    resolved_val = context.resolve_value(key)
    return (
        AssetKey.from_user_string(resolved_val) if isinstance(resolved_val, str) else resolved_val
    )


@resolver(fromtype=AssetDepSchema, totype=AssetDep)
class AssetDepResolver(Resolver[AssetDepSchema]):
    def resolve_asset(self, context: ResolutionContext) -> AssetKey:
        return _resolve_asset_key(self.schema.asset, context)


@resolver(fromtype=AssetSpecSchema, totype=AssetSpec)
class AssetSpecResolver(Resolver[AssetSpecSchema]):
    def resolve_key(self, context: ResolutionContext) -> AssetKey:
        return _resolve_asset_key(self.schema.key, context)


@resolver(fromtype=AssetAttributesSchema)
class AssetAttributesResolver(Resolver[AssetAttributesSchema]):
    def resolve_key(self, context: ResolutionContext) -> Optional[AssetKey]:
        return _resolve_asset_key(self.schema.key, context) if self.schema.key else None

    def resolve(self, context: ResolutionContext) -> Mapping[str, Any]:
        # only include fields that are explcitly set
        set_fields = self.schema.model_dump(exclude_unset=True).keys()
        return {k: v for k, v in self.get_resolved_fields(context).items() if k in set_fields}
