import dagster as dg
from dagster._core.definitions.metadata import MetadataValue


def test_source_asset_metadata():
    sa = dg.SourceAsset(key=dg.AssetKey("foo"), metadata={"foo": "bar", "baz": object()})
    assert sa.metadata == {
        "foo": MetadataValue.text("bar"),
        "baz": MetadataValue.text("[object] (unserializable)"),
    }


def test_source_asset_key_args():
    assert dg.SourceAsset(key="foo").key == dg.AssetKey(["foo"])
    assert dg.SourceAsset(key=["bar", "foo"]).key == dg.AssetKey(["bar", "foo"])


def test_source_asset_with_bare_resource():
    class BareResourceObject:
        pass

    source_asset = dg.SourceAsset(key="foo", resource_defs={"bare_resource": BareResourceObject()})

    assert isinstance(source_asset.resource_defs["bare_resource"], dg.ResourceDefinition)
