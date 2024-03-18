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
    for stream, config in replication_config.get("streams", {}).items():
        if config and config.get("disabled", False):
            continue
        yield {"name": stream, "config": config}


def sling_assets(
    *,
    replication_config: SlingReplicationParam,
    dagster_sling_translator: DagsterSlingTranslator = DagsterSlingTranslator(),
    name: Optional[str] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    backfill_policy: Optional[BackfillPolicy] = None,
    op_tags: Optional[Mapping[str, Any]] = None,
) -> Callable[..., AssetsDefinition]:
    """Create a definition for how to materialize a set of Sling replication streams as Dagster assets, as
    described by a Sling replication config. This will create on Asset for every Sling target stream.

    A Sling Replication config is a configuration that maps sources to destinations. For the full
    spec and descriptions, see `Sling's Documentation <https://docs.slingdata.io/sling-cli/run/configuration>`_.

    Args:
        replication_config (Union[Mapping[str, Any], str, Path]): A path to a Sling replication config, or a dictionary
            of a replication config.
        dagster_sling_translator: (DagsterSlingTranslator): Allows customization of how to map a Sling stream to a Dagster
          AssetKey.
        name (Optional[str]: The name of the op.
        partitions_def (Optional[PartitionsDefinition]): The partitions definition for this asset.
        backfill_policy (Optional[BackfillPolicy]): The backfill policy for this asset.
        op_tags (Optional[Mapping[str, Any]]): The tags for this asset.

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
    """
    replication_config = validate_replication(replication_config)
    streams = get_streams_from_replication(replication_config)
    code_version = non_secure_md5_hash_str(str(replication_config).encode())

    specs: list[AssetSpec] = []
    for stream in streams:
        specs.append(
            AssetSpec(
                key=dagster_sling_translator.get_asset_key(stream),
                deps=dagster_sling_translator.get_deps_asset_key(stream),
                description=dagster_sling_translator.get_description(stream),
                metadata=dagster_sling_translator.get_metadata(stream),
                group_name=dagster_sling_translator.get_group_name(stream),
                freshness_policy=dagster_sling_translator.get_freshness_policy(stream),
                auto_materialize_policy=dagster_sling_translator.get_auto_materialize_policy(
                    stream
                ),
                code_version=code_version,
            )
        )

    def inner(fn) -> AssetsDefinition:
        asset_definition = multi_asset(
            name=name,
            compute_kind="sling",
            partitions_def=partitions_def,
            can_subset=False,
            op_tags=op_tags,
            backfill_policy=backfill_policy,
            specs=specs,
        )(fn)

        return asset_definition

    return inner
