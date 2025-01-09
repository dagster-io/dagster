from collections.abc import Sequence

from dagster import AssetMaterialization

from dagster_census.types import CensusOutput


def generate_materialization(
    census_output: CensusOutput, asset_key_prefix: Sequence[str]
) -> AssetMaterialization:
    sync_id = census_output.sync_run["sync_id"]
    source_name = census_output.source["name"]
    destination_name = census_output.destination["name"]

    metadata = {
        "sync_id": sync_id,
        "sync_run_id": census_output.sync_run["id"],
        "source_name": source_name,
        "source_type": census_output.source["type"],
        "destination_name": destination_name,
        "source_record_count": census_output.sync_run["source_record_count"],
        "records_processed": census_output.sync_run["records_processed"],
        "records_updated": census_output.sync_run["records_updated"],
        "records_failed": census_output.sync_run["records_failed"],
        "records_invalid": census_output.sync_run["records_invalid"],
        "full_sync": census_output.sync_run["full_sync"],
    }

    asset_key_name = [*asset_key_prefix, f"sync_{sync_id}"]

    return AssetMaterialization(
        asset_key=asset_key_name,
        description=(
            f"Sync generated for Census sync {sync_id}: {source_name} to {destination_name}"
        ),
        metadata=metadata,
    )
