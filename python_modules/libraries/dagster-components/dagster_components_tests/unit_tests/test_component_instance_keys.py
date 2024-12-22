import pytest
from dagster._check.functions import CheckError
from dagster_components.core.component import ComponentInstanceKey


def test_basic_component_instance_key() -> None:
    assert ComponentInstanceKey(parts=[])
    assert ComponentInstanceKey(parts=[]).dot_path == ""
    assert ComponentInstanceKey.root()
    assert ComponentInstanceKey.root().dot_path == ""
    assert ComponentInstanceKey(parts=["a", "b", "c"])
    assert ComponentInstanceKey(parts=["a", "b", "c"]).dot_path == "a.b.c"


def test_invalid_component_instance_key() -> None:
    with pytest.raises(CheckError):
        ComponentInstanceKey(parts=[".a", "b", "c"])


def test_component_instance_key_child() -> None:
    assert ComponentInstanceKey(parts=["a", "b"]).child("c").dot_path == "a.b.c"
    with pytest.raises(CheckError):
        ComponentInstanceKey(parts=["a", "b", "c"]).child(".d")
