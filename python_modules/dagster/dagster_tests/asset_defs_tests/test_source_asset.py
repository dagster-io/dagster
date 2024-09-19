from dagster._core.definitions import ResourceDefinition, SourceAsset
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import MetadataValue


def test_source_asset_metadata():
    sa = SourceAsset(key=AssetKey("foo"), metadata={"foo": "bar", "baz": object()})
    assert sa.metadata == {
        "foo": MetadataValue.text("bar"),
        "baz": MetadataValue.text("[object] (unserializable)"),
    }


def test_source_asset_key_args():
    assert SourceAsset(key="foo").key == AssetKey(["foo"])
    assert SourceAsset(key=["bar", "foo"]).key == AssetKey(["bar", "foo"])


def test_source_asset_with_bare_resource():
    class BareResourceObject:
        pass

    source_asset = SourceAsset(key="foo", resource_defs={"bare_resource": BareResourceObject()})

    assert isinstance(source_asset.resource_defs["bare_resource"], ResourceDefinition)
