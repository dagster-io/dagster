import pendulum
from dagster import AssetMaterialization, MetadataValue
from dagster._core.definitions.metadata import (
    FreshnessCheckMetadataSet,
    FreshnessMetadataSet,
)


def test_freshness_metadata_entries():
    freshness_metadata_entries = FreshnessMetadataSet(
        last_updated_timestamp=MetadataValue.timestamp(pendulum.parse("2020-04-12"))
    )

    dict_table_metadata_entries = dict(freshness_metadata_entries)
    assert dict_table_metadata_entries == {
        "dagster/last_updated_timestamp": MetadataValue.timestamp(pendulum.parse("2020-04-12"))
    }
    AssetMaterialization(asset_key="a", metadata=dict_table_metadata_entries)

    assert dict(FreshnessMetadataSet()) == {}
    assert FreshnessMetadataSet.extract(dict(FreshnessMetadataSet())) == FreshnessMetadataSet()


def test_freshness_check_metadata_entries():
    freshness_metadata_entries = FreshnessCheckMetadataSet(
        overdue_deadline_timestamp=MetadataValue.timestamp(pendulum.parse("2020-04-12")),
        overdue_seconds=54.8,
    )

    dict_table_metadata_entries = dict(freshness_metadata_entries)
    assert dict_table_metadata_entries == {
        "dagster/overdue_deadline_timestamp": MetadataValue.timestamp(pendulum.parse("2020-04-12")),
        "dagster/overdue_seconds": 54.8,
    }
    AssetMaterialization(asset_key="a", metadata=dict_table_metadata_entries)

    assert dict(FreshnessCheckMetadataSet()) == {}
    assert (
        FreshnessCheckMetadataSet.extract(dict(FreshnessCheckMetadataSet()))
        == FreshnessCheckMetadataSet()
    )
