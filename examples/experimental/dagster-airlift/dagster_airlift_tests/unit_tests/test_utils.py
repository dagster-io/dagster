import pytest
from dagster import AssetKey, AssetSpec, asset, multi_asset
from dagster._check.functions import CheckError
from dagster_airlift.core.utils import get_dag_id_from_asset, get_task_id_from_asset


def test_no_convention() -> None:
    """Test that we don't error when no convention method for setting dag and task id are provided."""

    @asset
    def no_op():
        pass

    assert get_dag_id_from_asset(no_op) is None
    assert get_task_id_from_asset(no_op) is None


def test_retrieve_by_asset_tag() -> None:
    """Test that we can retrieve the dag and task id from the asset tags. Test that error edge cases are properly handled."""

    # 1. Single spec retrieval
    @asset(tags={"airlift/dag_id": "print_dag", "airlift/task_id": "print_task"})
    def one_spec():
        pass

    assert get_dag_id_from_asset(one_spec) == "print_dag"
    assert get_task_id_from_asset(one_spec) == "print_task"

    # 2. Multiple spec retrieval, all specs match
    @multi_asset(
        specs=[
            AssetSpec(
                key=AssetKey(["simple"]),
                tags={"airlift/dag_id": "print_dag", "airlift/task_id": "print_task"},
            ),
            AssetSpec(
                key=AssetKey(["other"]),
                tags={"airlift/dag_id": "print_dag", "airlift/task_id": "print_task"},
            ),
        ]
    )
    def multi_spec_pass():
        pass

    assert get_dag_id_from_asset(multi_spec_pass) == "print_dag"
    assert get_task_id_from_asset(multi_spec_pass) == "print_task"

    # 3. Multiple spec retrieval but with different tasks/dags
    @multi_asset(
        specs=[
            AssetSpec(
                key=AssetKey(["simple"]),
                tags={"airlift/dag_id": "print_dag", "airlift/task_id": "print_task"},
            ),
            AssetSpec(
                key=AssetKey(["other"]),
                tags={"airlift/dag_id": "other_dag", "airlift/task_id": "other_task"},
            ),
        ]
    )
    def multi_spec_mismatch():
        pass

    with pytest.raises(CheckError):
        get_dag_id_from_asset(multi_spec_mismatch)
    with pytest.raises(CheckError):
        get_task_id_from_asset(multi_spec_mismatch)

    # 5. Multiple spec retrieval, not all have tags set
    @multi_asset(
        specs=[
            AssetSpec(
                key=AssetKey(["simple"]),
                tags={"airlift/dag_id": "print_dag", "airlift/task_id": "print_task"},
            ),
            AssetSpec(key=AssetKey(["other"])),
        ]
    )
    def multi_spec_task_mismatch():
        pass

    with pytest.raises(CheckError):
        get_dag_id_from_asset(multi_spec_task_mismatch)

    with pytest.raises(CheckError):
        get_task_id_from_asset(multi_spec_task_mismatch)


def test_retrieve_by_op_tag() -> None:
    """Test that we can retrieve the dag and task id from the op tags."""

    @asset(op_tags={"airlift/dag_id": "print_dag", "airlift/task_id": "print_task"})
    def the_asset():
        pass

    assert get_dag_id_from_asset(the_asset) == "print_dag"
    assert get_task_id_from_asset(the_asset) == "print_task"


def test_retrieve_by_name() -> None:
    """Test that we can retrieve the dag and task id from the name."""

    @asset
    def print_dag__print_task():
        pass

    assert get_dag_id_from_asset(print_dag__print_task) == "print_dag"
    assert get_task_id_from_asset(print_dag__print_task) == "print_task"


def test_op_asset_tag_mismatch() -> None:
    @asset(
        tags={"airlift/dag_id": "print_dag", "airlift/task_id": "print_task"},
        op_tags={"airlift/dag_id": "other_dag", "airlift/task_id": "other_task"},
    )
    def mismatched():
        pass

    with pytest.raises(CheckError):
        get_dag_id_from_asset(mismatched)

    with pytest.raises(CheckError):
        get_task_id_from_asset(mismatched)


def test_op_asset_name_mismatch() -> None:
    @asset(tags={"airlift/dag_id": "print_dag", "airlift/task_id": "print_task"})
    def other_dag__other_task():
        pass

    with pytest.raises(CheckError):
        get_dag_id_from_asset(other_dag__other_task)

    with pytest.raises(CheckError):
        get_task_id_from_asset(other_dag__other_task)


def test_op_tag_name_mismatch() -> None:
    @asset(op_tags={"airlift/dag_id": "print_dag", "airlift/task_id": "print_task"})
    def other_dag__other_task():
        pass

    with pytest.raises(CheckError):
        get_dag_id_from_asset(other_dag__other_task)

    with pytest.raises(CheckError):
        get_task_id_from_asset(other_dag__other_task)
