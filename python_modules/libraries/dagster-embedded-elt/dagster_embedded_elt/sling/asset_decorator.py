import hashlib
from typing import Any, Callable, Iterable, Mapping, Optional

from dagster import (
    AssetsDefinition,
    AssetSpec,
    BackfillPolicy,
    PartitionsDefinition,
    multi_asset,
)

from dagster_embedded_elt.sling.dagster_sling_translator import DagsterSlingTranslator
from dagster_embedded_elt.sling.sling_replication import SlingReplicationParam, validate_replication


def get_streams_from_replication(
    replication_config: Mapping[str, Any],
) -> Iterable[Mapping[str, Any]]:
    """Returns the set of streams from a Sling replication config."""
    return [
        {"name": stream, "config": config}
        for stream, config in replication_config.get("streams", {}).items()
    ]


def sling_assets(
    *,
    replication_config: SlingReplicationParam,
    dagster_sling_translator: DagsterSlingTranslator = DagsterSlingTranslator(),
    partitions_def: Optional[PartitionsDefinition] = None,
    backfill_policy: Optional[BackfillPolicy] = None,
    op_tags: Optional[Mapping[str, Any]] = None,
) -> Callable[..., AssetsDefinition]:
    """Create a definition for how to materialize a Sling replication stream as a Dagster Asset, as
    described by a Sling replication config. This will create on Asset for every Sling target stream.

    Args:
        replication_config: SlingReplicationParam: A path to a Sling replication config, or a dictionary of a replication config.
        dagster_sling_translator: DagsterSlingTranslator: Allows customization of how to map a Sling stream to a Dagster AssetKey.
        partitions_def: Optional[PartitionsDefinition]: The partitions definition for this asset.
        backfill_policy: Optional[BackfillPolicy]: The backfill policy for this asset.
        op_tags: Optional[Mapping[str, Any]]: The tags for this asset.

    Examples:
        # TODO: Add examples once API is complete
    """
    replication_config = validate_replication(replication_config)
    streams = get_streams_from_replication(replication_config)

    group_name = dagster_sling_translator.get_group_name(replication_config)
    code_version = hashlib.md5(str(replication_config).encode(), usedforsecurity=False).hexdigest()
    freshness_policy = dagster_sling_translator.get_freshness_policy(replication_config)
    auto_materialize_policy = dagster_sling_translator.get_auto_materialize_policy(
        replication_config
    )

    specs: list[AssetSpec] = []
    for stream in streams:
        specs.append(
            AssetSpec(
                key=dagster_sling_translator.get_asset_key(stream),
                deps=dagster_sling_translator.get_deps_asset_key(stream),
                group_name=group_name,
                code_version=code_version,
                freshness_policy=freshness_policy,
                auto_materialize_policy=auto_materialize_policy,
            )
        )

    def inner(fn) -> AssetsDefinition:
        asset_definition = multi_asset(
            name="sling_asset_definition",
            compute_kind="sling",
            partitions_def=partitions_def,
            can_subset=False,
            op_tags=op_tags,
            backfill_policy=backfill_policy,
            specs=specs,
        )(fn)

        return asset_definition

    return inner
