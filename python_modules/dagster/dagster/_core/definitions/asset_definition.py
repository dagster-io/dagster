from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Sequence, Union

from dagster._core.definitions.asset_dep import CoercibleToAssetDep
from dagster._core.definitions.asset_key import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.node_definition import NodeDefinition
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._utils.warnings import disable_dagster_warnings


class AssetDefinition(AssetsDefinition):
    def __init__(
        self,
        key: CoercibleToAssetKey,
        *,
        keys_by_input_name: Mapping[str, AssetKey] = {},
        output_name: Optional[str] = None,
        node_def: Optional[NodeDefinition] = None,
        deps: Iterable[CoercibleToAssetDep],
        description: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        group_name: Optional[str] = None,
        skippable: bool = False,
        code_version: Optional[str] = None,
        auto_materialize_policy: Optional[AutoMaterializePolicy] = None,
        freshness_policy: Optional[FreshnessPolicy] = None,
        owners: Optional[Sequence[str]] = None,
        tags: Optional[Mapping[str, str]] = None,
        partitions_def: Optional[PartitionsDefinition] = None,
        backfill_policy: Optional[BackfillPolicy] = None,
        resource_defs: Optional[Mapping[str, object]] = None,
    ):
        with disable_dagster_warnings():
            spec = AssetSpec.dagster_internal_init(
                key=key,
                description=description,
                metadata=metadata,
                group_name=group_name,
                skippable=skippable,
                code_version=code_version,
                auto_materialize_policy=auto_materialize_policy,
                owners=owners,
                tags=tags,
                deps=deps,
                freshness_policy=freshness_policy,
            )

            super().__init__(
                keys_by_input_name=keys_by_input_name,
                keys_by_output_name={output_name: spec.key} if output_name else {},
                node_def=node_def,
                partitions_def=partitions_def,
                backfill_policy=backfill_policy,
                resource_defs=resource_defs,
                specs=[spec],
            )

    @staticmethod
    def dagster_internal_init(
        *,
        key: CoercibleToAssetKey,
        keys_by_input_name: Mapping[str, AssetKey],
        output_name: Optional[str],
        node_def: Optional[NodeDefinition],
        deps: Iterable[CoercibleToAssetDep],
        description: Optional[str],
        metadata: Optional[Mapping[str, Any]],
        group_name: Optional[str],
        skippable: bool,
        code_version: Optional[str],
        auto_materialize_policy: Optional[AutoMaterializePolicy],
        freshness_policy: Optional[FreshnessPolicy],
        owners: Optional[Sequence[str]],
        tags: Optional[Mapping[str, str]],
        partitions_def: Optional[PartitionsDefinition],
        backfill_policy: Optional[BackfillPolicy],
        resource_defs: Optional[Mapping[str, object]],
    ) -> "AssetDefinition":
        return AssetDefinition(
            key=key,
            keys_by_input_name=keys_by_input_name,
            output_name=output_name,
            node_def=node_def,
            deps=deps,
            description=description,
            metadata=metadata,
            group_name=group_name,
            skippable=skippable,
            code_version=code_version,
            auto_materialize_policy=auto_materialize_policy,
            freshness_policy=freshness_policy,
            owners=owners,
            tags=tags,
            partitions_def=partitions_def,
            backfill_policy=backfill_policy,
            resource_defs=resource_defs,
        )

    def get_attributes_dict(self) -> Dict[str, Any]:
        spec = next(iter(self.specs))
        return {
            **spec._asdict(),
            **dict(
                keys_by_input_name=self._keys_by_input_name,
                output_name=next(iter(self._keys_by_output_name.keys()))
                if self._keys_by_output_name
                else None,
                node_def=self._node_def,
                partitions_def=self._partitions_def,
                resource_defs=self._resource_defs,
                backfill_policy=self._backfill_policy,
            ),
        }

    def with_attributes(
        self,
        *,
        output_asset_key_replacements: Mapping[AssetKey, AssetKey] = {},
        input_asset_key_replacements: Mapping[AssetKey, AssetKey] = {},
        group_names_by_key: Mapping[AssetKey, str] = {},
        tags_by_key: Mapping[AssetKey, Mapping[str, str]] = {},
        freshness_policy: Optional[
            Union[FreshnessPolicy, Mapping[AssetKey, FreshnessPolicy]]
        ] = None,
        auto_materialize_policy: Optional[
            Union[AutoMaterializePolicy, Mapping[AssetKey, AutoMaterializePolicy]]
        ] = None,
        backfill_policy: Optional[BackfillPolicy] = None,
    ) -> "AssetsDefinition":
        auto_materialize_policy = (
            auto_materialize_policy.get(self.key)
            if isinstance(auto_materialize_policy, Mapping)
            else auto_materialize_policy
        )
        freshness_policy = (
            freshness_policy.get(self.key)
            if isinstance(freshness_policy, Mapping)
            else freshness_policy
        )

        spec = next(iter(self.specs))
        if input_asset_key_replacements or output_asset_key_replacements:
            deps = []
            for dep in spec.deps:
                replacement_key = input_asset_key_replacements.get(
                    dep.asset_key,
                    output_asset_key_replacements.get(dep.asset_key),
                )
                if replacement_key is not None:
                    deps.append(dep._replace(asset_key=replacement_key))
                else:
                    deps.append(dep)
        else:
            deps = spec.deps

        return AssetDefinition.dagster_internal_init(
            **{
                **spec._asdict(),
                **dict(
                    key=output_asset_key_replacements.get(self.key, self.key),
                    keys_by_input_name={
                        input_name: input_asset_key_replacements.get(key, key)
                        for input_name, key in self._keys_by_input_name.items()
                    },
                    output_name=next(iter(self.keys_by_output_name.keys())),
                    node_def=self.node_def,
                    partitions_def=self.partitions_def,
                    resource_defs=self.resource_defs,
                    backfill_policy=backfill_policy or self.backfill_policy,
                    group_name=group_names_by_key.get(self.key, spec.group_name),
                    auto_materialize_policy=auto_materialize_policy or spec.auto_materialize_policy,
                    freshness_policy=freshness_policy or spec.freshness_policy,
                    tags=tags_by_key.get(self.key, spec.tags),
                    deps=deps,
                ),
            }
        )

    def map_asset_specs(self, fn: Callable[[AssetSpec], AssetSpec]) -> "AssetsDefinition":
        spec = next(iter(self.specs))
        mapped_spec = fn(spec)
        if mapped_spec.key != spec.key:
            raise DagsterInvalidDefinitionError(
                f"Asset key {spec.key.to_user_string()} was changed to "
                f"{mapped_spec.key.to_user_string()}. Mapping function must not change keys."
            )

        return AssetDefinition.dagster_internal_init(
            **{**self.get_attributes_dict(), **mapped_spec._asdict()}
        )
