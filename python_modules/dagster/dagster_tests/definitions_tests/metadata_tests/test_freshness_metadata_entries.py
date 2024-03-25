import pendulum
from dagster import AssetMaterialization, MetadataValue
from dagster._core.definitions.metadata import (
    FreshnessCheckMetadataEntries,
    FreshnessMetadataEntries,
)


def test_freshness_metadata_entries():
    freshness_metadata_entries = FreshnessMetadataEntries(
        last_updated_timestamp=MetadataValue.timestamp(pendulum.parse("2020-04-12"))
    )

    dict_table_metadata_entries = dict(freshness_metadata_entries)
    assert dict_table_metadata_entries == {
        "dagster/last_updated_timestamp": MetadataValue.timestamp(pendulum.parse("2020-04-12"))
    }
    AssetMaterialization(asset_key="a", metadata=dict_table_metadata_entries)

    assert dict(FreshnessMetadataEntries()) == {}
    assert (
        FreshnessMetadataEntries.extract(dict(FreshnessMetadataEntries()))
        == FreshnessMetadataEntries()
    )


def test_freshness_check_metadata_entries():
    freshness_metadata_entries = FreshnessCheckMetadataEntries(
        overdue_deadline_timestamp=MetadataValue.timestamp(pendulum.parse("2020-04-12")),
        overdue_minutes=54.8,
    )

    dict_table_metadata_entries = dict(freshness_metadata_entries)
    assert dict_table_metadata_entries == {
        "dagster/overdue_deadline_timestamp": MetadataValue.timestamp(pendulum.parse("2020-04-12")),
        "dagster/overdue_minutes": 54.8,
    }
    AssetMaterialization(asset_key="a", metadata=dict_table_metadata_entries)

    assert dict(FreshnessCheckMetadataEntries()) == {}
    assert (
        FreshnessCheckMetadataEntries.extract(dict(FreshnessCheckMetadataEntries()))
        == FreshnessCheckMetadataEntries()
    )
