import pytest
from dagster import AssetKey, AssetSpec, JsonMetadataValue, asset, multi_asset
from dagster._check.functions import CheckError
from dagster_airlift.constants import AIRFLOW_COUPLING_METADATA_KEY
from dagster_airlift.core.utils import get_couplings_from_asset


def test_no_convention() -> None:
    """Test that we don't error when no convention method for setting dag and task id are provided."""

    @asset
    def no_op():
        pass

    assert get_couplings_from_asset(no_op) is None


def test_retrieve_by_asset_metadata() -> None:
    """Test that we can retrieve the dag and task id from the asset metadata. Test that error edge cases are properly handled."""

    # 1. Single spec retrieval
    @asset(
        metadata={AIRFLOW_COUPLING_METADATA_KEY: JsonMetadataValue([("print_dag", "print_task")])}
    )
    def one_spec():
        pass

    assert get_couplings_from_asset(one_spec) == [("print_dag", "print_task")]

    # 2. Multiple spec retrieval, all specs match
    @multi_asset(
        specs=[
            AssetSpec(
                key=AssetKey(["simple"]),
                metadata={
                    AIRFLOW_COUPLING_METADATA_KEY: JsonMetadataValue([("print_dag", "print_task")])
                },
            ),
            AssetSpec(
                key=AssetKey(["other"]),
                metadata={
                    AIRFLOW_COUPLING_METADATA_KEY: JsonMetadataValue([("print_dag", "print_task")])
                },
            ),
        ]
    )
    def multi_spec_pass():
        pass

    assert get_couplings_from_asset(multi_spec_pass) == [("print_dag", "print_task")]

    # 3. Multiple spec retrieval but with different tasks/dags
    @multi_asset(
        specs=[
            AssetSpec(
                key=AssetKey(["simple"]),
                metadata={
                    AIRFLOW_COUPLING_METADATA_KEY: JsonMetadataValue([("print_dag", "print_task")])
                },
            ),
            AssetSpec(
                key=AssetKey(["other"]),
                metadata={
                    AIRFLOW_COUPLING_METADATA_KEY: JsonMetadataValue([("other_dag", "other_task")])
                },
            ),
        ]
    )
    def multi_spec_mismatch():
        pass

    with pytest.raises(CheckError):
        get_couplings_from_asset(multi_spec_mismatch)

    # 5. Multiple spec retrieval, not all have tags set
    @multi_asset(
        specs=[
            AssetSpec(
                key=AssetKey(["simple"]),
                metadata={
                    AIRFLOW_COUPLING_METADATA_KEY: JsonMetadataValue([("print_dag", "print_task")])
                },
            ),
            AssetSpec(key=AssetKey(["other"])),
        ]
    )
    def multi_spec_task_mismatch():
        pass

    with pytest.raises(CheckError):
        get_couplings_from_asset(multi_spec_task_mismatch)
