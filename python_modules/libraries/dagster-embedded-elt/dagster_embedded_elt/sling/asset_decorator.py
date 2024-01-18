from typing import Any, Callable, Iterable, Mapping, Optional

from dagster import (
    AssetsDefinition,
    AssetSpec,
    BackfillPolicy,
    PartitionsDefinition,
    multi_asset,
)
from dagster._utils.security import non_secure_md5_hash_str

from dagster_embedded_elt.sling.dagster_sling_translator import DagsterSlingTranslator
from dagster_embedded_elt.sling.sling_replication import SlingReplicationParam, validate_replication


def get_streams_from_replication(
    replication_config: Mapping[str, Any],
) -> Iterable[Mapping[str, Any]]:
    """Returns a list of streams and their configs from a Sling replication config."""
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

    A Sling Replication config is a configuration that maps sources to destinations. For the full
    spec and descriptions, see `Sling's Documentation <https://docs.slingdata.io/sling-cli/run/configuration>`_.

    Args:
        replication_config: SlingReplicationParam: A path to a Sling replication config, or a dictionary of a replication config.
        dagster_sling_translator: DagsterSlingTranslator: Allows customization of how to map a Sling stream to a Dagster AssetKey.
        partitions_def: Optional[PartitionsDefinition]: The partitions definition for this asset.
        backfill_policy: Optional[BackfillPolicy]: The backfill policy for this asset.
        op_tags: Optional[Mapping[str, Any]]: The tags for this asset.

    Examples:
        Running a sync by providing a path to a Sling Replication config:

        .. code-block:: python

            from dagster_embedded_elt.sling import sling_assets, SlingResource, SlingConnectionResource

            sling_resource = SlingResource(
                connections=[
                    SlingConnectionResource(
                        name="MY_POSTGRES", type="postgres", connection_string=EnvVar("POSTGRES_URL")
                    ),
                    SlingConnectionResource(
                        name="MY_DUCKDB",
                        type="duckdb",
                        connection_string="duckdb:///var/tmp/duckdb.db",
                    ),
                ]
            )

            config_path = "/path/to/replication.yaml"
            @sling_assets(replication_config=config_path)
            def my_assets(context, sling: SlingResource):
                for lines in sling.replicate(
                    replication_config=config_path,
                    dagster_sling_translator=DagsterSlingTranslator(),
                ):
                    context.log.info(lines)

        Running a sync using a custom translator:
    """
    replication_config = validate_replication(replication_config)
    streams = get_streams_from_replication(replication_config)

    group_name = dagster_sling_translator.get_group_name(replication_config)
    code_version = non_secure_md5_hash_str(str(replication_config).encode())
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
