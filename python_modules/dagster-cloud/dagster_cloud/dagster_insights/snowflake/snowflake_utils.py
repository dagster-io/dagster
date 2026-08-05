from uuid import uuid4 as uuid

from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetObservation,
    JobDefinition,
    OpExecutionContext,
)

# Metadata key prefix used to tag Snowflake queries with opaque IDs
OPAQUE_ID_METADATA_KEY_PREFIX = "dagster_snowflake_opaque_id:"
OPAQUE_ID_SQL_SIGIL = "snowflake_dagster_dbt_v1_opaque_id"

OUTPUT_NON_ASSET_SIGIL = "__snowflake_query_metadata_"


def build_opaque_id_metadata(opaque_id: str) -> dict:
    return {f"{OPAQUE_ID_METADATA_KEY_PREFIX}{opaque_id}": True}


def meter_snowflake_query(
    context: OpExecutionContext | AssetExecutionContext,
    sql: str,
    comment_factory=lambda comment: f"\n-- {comment}\n",
    opaque_id=None,
    associated_asset_key: AssetKey | None = None,
):
    """A utility function that takes a SQL query and returns a modified version of the query
    that includes a comment that will be used to identify the query when attributing cost.
    Logs an AssetObservation event to associate the query with the executing op/asset.

    .. code-block:: python

        from dagster import asset, AssetExecutionContext
        from dagster_snowflake import SnowflakeResource
        from dagster_cloud.dagster_insights import meter_snowflake_query

        @asset
        def my_cool_asset(
            context: AssetExecutionContext, snowflake: SnowflakeResource
        ) -> Dict[str, Any]:
            with snowflake.get_connection() as conn:
                res = conn.execute_query(meter_snowflake_query(context, "SELECT * FROM my_big_table"), fetch_results=True)

            return res

    """
    if context.has_assets_def and len(context.assets_def.keys_by_output_name.keys()) == 1:
        inferred_asset_key = context.asset_key
        if associated_asset_key and associated_asset_key != inferred_asset_key:
            raise RuntimeError(
                f"Op materializes asset key {inferred_asset_key}, which does not match supplied"
                f" asset key {associated_asset_key}"
            )
        associated_asset_key = inferred_asset_key
    elif context.has_assets_def:
        asset_keys = context.assets_def.keys_by_output_name.values()

        if not associated_asset_key:
            context.log.warn(
                "Op materializes assets, but no asset key associated with Snowflake query usage."
            )
        if associated_asset_key and associated_asset_key not in asset_keys:
            raise RuntimeError(
                f"Op materializes assets {asset_keys}, but supplied asset key"
                f" {associated_asset_key} not found"
            )
    elif not context.has_assets_def and associated_asset_key:
        raise RuntimeError(
            f"Op does not materialize assets, but supplied asset key {associated_asset_key} found"
        )

    associated_output_name = None
    if associated_asset_key:
        associated_output_name = context.assets_def.get_output_name_for_asset_key(
            associated_asset_key
        )

    if opaque_id is None:
        opaque_id = str(uuid())
    modified_sql = sql + comment_factory(f"{OPAQUE_ID_SQL_SIGIL}[[[{opaque_id}]]]")

    if associated_output_name and associated_asset_key:
        context.log_event(
            AssetObservation(
                asset_key=associated_asset_key,
                metadata=build_opaque_id_metadata(opaque_id),
            )
        )
    else:
        context.log_event(
            AssetObservation(
                asset_key=marker_asset_key_for_job(context.job_def),
                metadata=build_opaque_id_metadata(opaque_id),
            )
        )

    return modified_sql


def marker_asset_key_for_job(
    job: JobDefinition,
) -> AssetKey:
    return AssetKey(path=[f"{OUTPUT_NON_ASSET_SIGIL}{job.name}"])
