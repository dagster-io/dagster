from typing import Any, Callable, Iterable, List, Mapping, Optional

from dagster import (
    AssetsDefinition,
    AssetSpec,
    BackfillPolicy,
    FreshnessPolicy,
    PartitionsDefinition,
    multi_asset,
)
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from sling.translator import DagsterSlingTranslator

from dagster_embedded_elt.sling.dagster_sling_translator import DagsterSlingTranslator
from dagster_embedded_elt.sling.sling_replication import SlingReplicationParam, validate_replication


def get_streams_from_replication(replication_config: Mapping[str, Any]) -> Iterable[str]:
    """Returns a list of streams from a Sling replication config.

    If an `asset_key` is provided, it will be used instead. For example, below the stream name
    will be read as `public.foo_users`


    .. code-block:: yaml

        streams:
          public.users:
            meta:
              dagster:
                asset_key: public.foo_users

    Args:
        replication_config: Mapping[str, Any]: A dictionary of a Sling replication config.
    """
    keys = []

    for key, value in replication_config["streams"].items():
        if isinstance(value, dict):
            asset_key_config = value.get("meta", {}).get("dagster", {}).get("asset_key", [])
            keys.append(asset_key_config if asset_key_config else key)
        else:
            keys.append(key)
    return keys


def sling_assets(
    *,
    replication_config: SlingReplicationParam,
    dagster_sling_translator: DagsterSlingTranslator = DagsterSlingTranslator(),
    partitions_def: Optional[PartitionsDefinition] = None,
    backfill_policy: Optional[BackfillPolicy] = None,
    op_tags: Optional[Mapping[str, Any]] = None,
    group_name: Optional[str] = None,
    code_version: Optional[str] = None,
    freshness_policy: Optional[FreshnessPolicy] = None,
    auto_materialize_policy: Optional[AutoMaterializePolicy] = None,
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
        group_name: Optional[str]: The group name for this asset.
        code_version: Optional[str]: The code version for this asset.
        freshness_policy: Optional[FreshnessPolicy]: The freshness policy for this asset.
        auto_materialize_policy: Optional[AutoMaterializePolicy]: The auto materialize policy for this asset.

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

    specs: List[AssetSpec] = []
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
