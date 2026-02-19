from typing import Union

import pytest
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.metadata.table import TableColumn, TableSchema
from dagster._core.definitions.tags import build_kind_tag_key
from dagster_sigma.translator import (
    DagsterSigmaTranslator,
    SigmaDataset,
    SigmaDatasetTranslatorData,
    SigmaOrganizationData,
    SigmaTable,
    SigmaWorkbook,
    SigmaWorkbookTranslatorData,
)

from dagster_sigma_tests.conftest import (
    SAMPLE_DATASET_DATA,
    SAMPLE_DATASET_INODE,
    SAMPLE_TABLE_DATA,
    SAMPLE_TABLE_INODE,
    SAMPLE_WORKBOOK_DATA,
)


def test_workbook_translation() -> None:
    sample_workbook = SigmaWorkbook(
        properties=SAMPLE_WORKBOOK_DATA,
        datasets={SAMPLE_DATASET_INODE},
        owner_email="ben@dagsterlabs.com",
        direct_table_deps={SAMPLE_TABLE_INODE},
        lineage=[],
        materialization_schedules=None,
    )

    sample_dataset = SigmaDataset(properties=SAMPLE_DATASET_DATA, columns=set(), inputs=set())

    translator = DagsterSigmaTranslator()

    asset_spec = translator.get_asset_spec(
        SigmaWorkbookTranslatorData(
            workbook=sample_workbook,
            organization_data=SigmaOrganizationData(
                workbooks=[sample_workbook],
                datasets=[sample_dataset],
                tables=[SigmaTable(properties=SAMPLE_TABLE_DATA)],
            ),
        )
    )

    assert asset_spec.key.path == ["Sample_Workbook"]
    assert asset_spec.metadata["dagster_sigma/web_url"].value == SAMPLE_WORKBOOK_DATA["url"]
    assert asset_spec.metadata["dagster_sigma/version"] == 5
    assert asset_spec.metadata["dagster_sigma/created_at"].value == 1726176169.072
    assert build_kind_tag_key("sigma") in asset_spec.tags
    assert build_kind_tag_key("workbook") in asset_spec.tags
    assert asset_spec.owners == ["ben@dagsterlabs.com"]
    assert {dep.asset_key for dep in asset_spec.deps} == {
        AssetKey(["Orders_Dataset"]),
        AssetKey(["my_database", "my_schema", "payments"]),
    }


def test_dataset_translation() -> None:
    sample_dataset = SigmaDataset(
        properties=SAMPLE_DATASET_DATA,
        columns={"user_id", "date", "order_id"},
        inputs={"TESTDB.JAFFLE_SHOP.STG_ORDERS"},
    )

    translator = DagsterSigmaTranslator()

    asset_spec = translator.get_asset_spec(
        SigmaDatasetTranslatorData(
            dataset=sample_dataset,
            organization_data=SigmaOrganizationData(
                workbooks=[], datasets=[sample_dataset], tables=[]
            ),
        )
    )

    assert asset_spec.key.path == ["Orders_Dataset"]
    assert asset_spec.metadata["dagster_sigma/web_url"].value == SAMPLE_DATASET_DATA["url"]
    assert asset_spec.metadata["dagster_sigma/created_at"].value == 1726175777.83
    assert asset_spec.metadata["dagster/column_schema"] == TableSchema(
        columns=[
            TableColumn(name="date"),
            TableColumn(name="order_id"),
            TableColumn(name="user_id"),
        ]
    )

    assert asset_spec.description == "Wow, cool orders dataset"

    assert build_kind_tag_key("sigma") in asset_spec.tags
    assert build_kind_tag_key("dataset") in asset_spec.tags
    assert {dep.asset_key for dep in asset_spec.deps} == {
        AssetKey(["testdb", "jaffle_shop", "stg_orders"])
    }


def test_dataset_translation_custom_translator() -> None:
    class MyCustomTranslator(DagsterSigmaTranslator):
        def get_asset_spec(
            self, data: Union[SigmaDatasetTranslatorData, SigmaWorkbookTranslatorData]
        ) -> AssetSpec:
            spec = super().get_asset_spec(data)
            if isinstance(data, SigmaDatasetTranslatorData):
                spec = spec.replace_attributes(
                    key=spec.key.with_prefix("sigma"), description="Custom description"
                )
            return spec

    sample_dataset = SigmaDataset(
        properties=SAMPLE_DATASET_DATA,
        columns={"user_id", "date", "order_id"},
        inputs={"TESTDB.JAFFLE_SHOP.STG_ORDERS"},
    )

    translator = MyCustomTranslator()

    asset_spec = translator.get_asset_spec(
        SigmaDatasetTranslatorData(
            dataset=sample_dataset,
            organization_data=SigmaOrganizationData(
                workbooks=[], datasets=[sample_dataset], tables=[]
            ),
        )
    )

    assert asset_spec.key.path == ["sigma", "Orders_Dataset"]
    assert asset_spec.description == "Custom description"


def test_workbook_translation_with_missing_table(caplog: pytest.LogCaptureFixture) -> None:
    """Test that workbook translation handles missing table inodes gracefully.

    This can happen when warn_on_lineage_fetch_error is True and some table
    metadata failed to fetch but table dependencies were still recorded.
    """
    # Create a workbook that references a table inode that doesn't exist
    missing_table_inode = "inode-MissingTableXYZ123"
    sample_workbook = SigmaWorkbook(
        properties=SAMPLE_WORKBOOK_DATA,
        datasets={SAMPLE_DATASET_INODE},
        owner_email="ben@dagsterlabs.com",
        direct_table_deps={SAMPLE_TABLE_INODE, missing_table_inode},  # One exists, one doesn't
        lineage=[],
        materialization_schedules=None,
    )

    sample_dataset = SigmaDataset(properties=SAMPLE_DATASET_DATA, columns=set(), inputs=set())

    translator = DagsterSigmaTranslator()

    # Organization data only has SAMPLE_TABLE_DATA, not the missing table
    asset_spec = translator.get_asset_spec(
        SigmaWorkbookTranslatorData(
            workbook=sample_workbook,
            organization_data=SigmaOrganizationData(
                workbooks=[sample_workbook],
                datasets=[sample_dataset],
                tables=[SigmaTable(properties=SAMPLE_TABLE_DATA)],  # Only one table
            ),
        )
    )

    # Should still generate a valid asset spec
    assert asset_spec.key.path == ["Sample_Workbook"]

    # Should include the dataset dependency
    dep_keys = {dep.asset_key for dep in asset_spec.deps}
    assert AssetKey(["Orders_Dataset"]) in dep_keys

    # Should include the table that was found
    assert AssetKey(["my_database", "my_schema", "payments"]) in dep_keys

    # Should only have these two dependencies (missing table should be skipped)
    assert len(dep_keys) == 2

    # Should have logged a warning about the missing table
    assert any(
        "not found in organization data" in record.message and missing_table_inode in record.message
        for record in caplog.records
    )
