import pytest
from dagster._check.functions import CheckError
from dagster_components.core.component import ComponentKey


def test_basic_component_key() -> None:
    assert ComponentKey(parts=[])
    assert ComponentKey(parts=[]).dot_path == ""
    assert ComponentKey.root()
    assert ComponentKey.root().dot_path == ""
    assert ComponentKey(parts=["a", "b", "c"])
    assert ComponentKey(parts=["a", "b", "c"]).dot_path == "a.b.c"


def test_invalid_component_key() -> None:
    with pytest.raises(CheckError):
        ComponentKey(parts=[".a", "b", "c"])


def test_component_key_child() -> None:
    assert ComponentKey(parts=["a", "b"]).child("c").dot_path == "a.b.c"
    with pytest.raises(CheckError):
        ComponentKey(parts=["a", "b", "c"]).child(".d") 