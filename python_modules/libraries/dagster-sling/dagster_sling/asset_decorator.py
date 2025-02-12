from collections.abc import Iterable, Mapping
from copy import deepcopy
from typing import Any, Callable, Optional

from dagster import (
    AssetsDefinition,
    BackfillPolicy,
    PartitionsDefinition,
    _check as check,
    multi_asset,
)
from dagster._utils.merger import deep_merge_dicts
from dagster._utils.security import non_secure_md5_hash_str

from dagster_sling.dagster_sling_translator import DagsterSlingTranslator
from dagster_sling.sling_replication import SlingReplicationParam, validate_replication

METADATA_KEY_TRANSLATOR = "dagster_sling/dagster_sling_translator"
METADATA_KEY_REPLICATION_CONFIG = "dagster_sling/sling_replication_config"


def get_streams_from_replication(
    replication_config: Mapping[str, Any],
) -> Iterable[Mapping[str, Any]]:
    """Returns a list of streams and their configs from a Sling replication config."""
    for stream, config in replication_config.get("streams", {}).items():
        if config and config.get("disabled", False):
            continue
        yield {"name": stream, "config": config}


def streams_with_default_dagster_meta(
    streams: Iterable[Mapping[str, Any]], replication_config: Mapping[str, Any]
) -> Iterable[Mapping[str, Any]]:
    """Ensures dagster meta configs in the `defaults` block of the replication_config are passed to
    the assets definition object.
    """
    default_dagster_meta = replication_config.get("defaults", {}).get("meta", {}).get("dagster", {})
    if not default_dagster_meta:
        yield from streams
    else:
        for stream in streams:
            name = stream["name"]
            config = deepcopy(stream["config"])
            if not config:
                config = {"meta": {"dagster": default_dagster_meta}}
            else:
                config["meta"] = deep_merge_dicts(
                    {"dagster": default_dagster_meta}, config.get("meta", {})
                )
            yield {"name": name, "config": config}


def sling_assets(
    *,
    replication_config: SlingReplicationParam,
    dagster_sling_translator: Optional[DagsterSlingTranslator] = None,
    name: Optional[str] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    backfill_policy: Optional[BackfillPolicy] = None,
    op_tags: Optional[Mapping[str, Any]] = None,
    pool: Optional[str] = None,
) -> Callable[[Callable[..., Any]], AssetsDefinition]:
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
        op_tags (Optional[Mapping[str, Any]]): The tags for the underlying op.
        pool (Optional[str]): A string that identifies the concurrency pool that governs the sling assets' execution.

    Examples:
        Running a sync by providing a path to a Sling Replication config:

        .. code-block:: python

            from dagster_sling import sling_assets, SlingResource, SlingConnectionResource

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
                yield from sling.replicate(context=context)
    """
    replication_config = validate_replication(replication_config)

    raw_streams = get_streams_from_replication(replication_config)

    streams = streams_with_default_dagster_meta(raw_streams, replication_config)

    code_version = non_secure_md5_hash_str(str(replication_config).encode())

    dagster_sling_translator = (
        check.opt_inst_param(
            dagster_sling_translator, "dagster_sling_translator", DagsterSlingTranslator
        )
        or DagsterSlingTranslator()
    )

    return multi_asset(
        name=name,
        partitions_def=partitions_def,
        can_subset=True,
        op_tags=op_tags,
        backfill_policy=backfill_policy,
        specs=[
            dagster_sling_translator.get_asset_spec(stream)
            .replace_attributes(code_version=code_version)
            .merge_attributes(
                metadata={
                    METADATA_KEY_TRANSLATOR: dagster_sling_translator,
                    METADATA_KEY_REPLICATION_CONFIG: replication_config,
                }
            )
            for stream in streams
        ],
        pool=pool,
    )
