from typing import (
    Sequence,
)

from dagster._serdes import whitelist_for_serdes
from dagster._serdes.ergonomics import serdes_tuple_class


def test_serdes_tuple_class_variant() -> None:
    class IAssetKey:
        path: Sequence[str]

    @whitelist_for_serdes
    class AssetKey(serdes_tuple_class(IAssetKey), IAssetKey): ...

    klass = serdes_tuple_class(IAssetKey)
    assert klass.__name__ == "_AssetKey"

    do_test(AssetKey)


def test_old_actual_class() -> None:
    from dagster._core.definitions.events import AssetKey

    do_test(AssetKey)


def do_test(klass) -> None:
    assert klass.__name__ == "AssetKey"
    assert klass(path=["foo", "bar"]).path == ["foo", "bar"]

    key_test = klass(path=["foo", "bar"])
    assert key_test.path == ["foo", "bar"]
