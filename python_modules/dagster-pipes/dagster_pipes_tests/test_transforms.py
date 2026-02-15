from typing import Annotated

import pytest
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.pipes.transforms import build_inprocess_transform_defs
from dagster_pipes.transforms.transform import (
    InMemoryStorageIO,
    StorageResult,
    TransformContext,
    TransformResult,
    Upstream,
    get_transform_metadata,
    get_upstream_metadata,
    is_transform_fn,
    mount_transform_graph,
    transform,
)


class DataFrame:
    """Example DataFrame class."""

    def is_column_null(self, col: str) -> bool:
        return False


def test_transform_metadata():
    @transform(assets=["prefix/foo"])
    def foo(
        context: TransformContext, upstream: Annotated[DataFrame, Upstream(asset="prefix/root")]
    ) -> TransformResult:
        return TransformResult.asset("prefix/foo", DataFrame())

    @transform(assets=["prefix/bar"])
    def bar(
        context: TransformContext, foo: Annotated[DataFrame, Upstream(asset="prefix/foo")]
    ) -> TransformResult:
        return TransformResult.asset("prefix/bar", DataFrame())

    @transform(checks=["prefix/bar/test_1"])
    def bar_col1_test(
        context: TransformContext, bar: Annotated[DataFrame, Upstream(asset="prefix/bar")]
    ) -> TransformResult:
        return TransformResult.check("prefix/bar/test_1", {"passed": True})

    # Test foo transform metadata
    assert is_transform_fn(foo)
    foo_metadata = get_transform_metadata(foo)
    assert foo_metadata.assets == ["prefix/foo"]
    assert foo_metadata.checks == []

    # Test bar transform metadata
    assert is_transform_fn(bar)
    bar_metadata = get_transform_metadata(bar)
    assert bar_metadata.assets == ["prefix/bar"]
    assert bar_metadata.checks == []

    # Test bar_col1_test transform metadata
    assert is_transform_fn(bar_col1_test)
    bar_col1_test_metadata = get_transform_metadata(bar_col1_test)
    assert bar_col1_test_metadata.assets == []
    assert bar_col1_test_metadata.checks == ["prefix/bar/test_1"]


def test_upstream_metadata():
    @transform(assets=["prefix/foo"])
    def foo(
        context: TransformContext, root: Annotated[DataFrame, Upstream(asset="prefix/root")]
    ) -> TransformResult:
        return TransformResult.asset("prefix/foo", DataFrame())

    @transform(assets=["prefix/bar"])
    def bar(
        context: TransformContext, foo: Annotated[DataFrame, Upstream(asset="prefix/foo")]
    ) -> TransformResult:
        return TransformResult.asset("prefix/bar", DataFrame())

    # Test foo upstream metadata
    root_metadata = get_upstream_metadata(foo, "root")
    assert isinstance(root_metadata, Upstream)
    assert root_metadata.asset == "prefix/root"

    # Test bar upstream metadata
    foo_metadata = get_upstream_metadata(bar, "foo")
    assert isinstance(foo_metadata, Upstream)
    assert foo_metadata.asset == "prefix/foo"


def test_transform_execution():
    @transform(assets=["prefix/foo"])
    def foo(
        context: TransformContext, upstream: Annotated[DataFrame, Upstream(asset="prefix/root")]
    ) -> TransformResult:
        return TransformResult.asset("prefix/foo", DataFrame())

    @transform(assets=["prefix/bar"])
    def bar(
        context: TransformContext, foo: Annotated[DataFrame, Upstream(asset="prefix/foo")]
    ) -> TransformResult:
        return TransformResult.asset("prefix/bar", DataFrame())

    # Test foo execution
    result = foo(TransformContext(), DataFrame())
    assert isinstance(result, TransformResult)
    assert "prefix/foo" in result.assets
    assert isinstance(result.assets["prefix/foo"], DataFrame)

    # Test bar execution
    result = bar(TransformContext(), DataFrame())
    assert isinstance(result, TransformResult)
    assert "prefix/bar" in result.assets
    assert isinstance(result.assets["prefix/bar"], DataFrame)


def test_mount_transform_graph():
    # Define transforms
    @transform(assets=["prefix/foo"])
    def foo(
        context: TransformContext, root: Annotated[DataFrame, Upstream(asset="prefix/root")]
    ) -> TransformResult:
        return TransformResult.asset("prefix/foo", DataFrame())

    @transform(assets=["prefix/bar"])
    def bar(
        context: TransformContext, foo: Annotated[DataFrame, Upstream(asset="prefix/foo")]
    ) -> TransformResult:
        return TransformResult.asset("prefix/bar", DataFrame())

    # Initialize storage with root data
    storage = InMemoryStorageIO()
    storage.save("prefix/root", DataFrame())

    # Mount transform graph
    with mount_transform_graph([foo, bar], storage) as graph:
        # Test execute_transform
        # Execute foo transform
        foo_result = graph.execute_transform(foo)
        assert isinstance(foo_result, StorageResult)
        assert "prefix/foo" in foo_result.assets
        assert isinstance(foo_result.assets["prefix/foo"], DataFrame)
        assert isinstance(storage.load("prefix/foo"), DataFrame)

        # Execute bar transform
        bar_result = graph.execute_transform(bar)
        assert isinstance(bar_result, StorageResult)
        assert "prefix/bar" in bar_result.assets
        assert isinstance(bar_result.assets["prefix/bar"], DataFrame)
        assert isinstance(storage.load("prefix/bar"), DataFrame)

        # Verify outputs were saved
        assert isinstance(storage.load("prefix/foo"), DataFrame)
        assert isinstance(storage.load("prefix/bar"), DataFrame)

        # Test execute_asset_key
        # Execute foo by asset key
        foo_result = graph.execute_asset_key("prefix/foo")
        assert isinstance(foo_result, StorageResult)
        assert "prefix/foo" in foo_result.assets
        assert isinstance(foo_result.assets["prefix/foo"], DataFrame)
        assert isinstance(storage.load("prefix/foo"), DataFrame)

        # Execute bar by asset key
        bar_result = graph.execute_asset_key("prefix/bar")
        assert isinstance(bar_result, StorageResult)
        assert "prefix/bar" in bar_result.assets
        assert isinstance(bar_result.assets["prefix/bar"], DataFrame)
        assert isinstance(storage.load("prefix/bar"), DataFrame)

        # Test error case for non-existent asset
        with pytest.raises(
            ValueError, match="No transform found that produces asset prefix/nonexistent"
        ):
            graph.execute_asset_key("prefix/nonexistent")


def test_transform_to_assets():
    """Test converting a transform graph to Dagster assets."""

    # Define transforms
    @transform(assets=["prefix/root"])
    def root(context) -> TransformResult:
        return TransformResult.asset("prefix/root", DataFrame())

    @transform(assets=["prefix/foo"])
    def foo(context, root: Annotated[DataFrame, Upstream(asset="prefix/root")]) -> TransformResult:
        return TransformResult.asset("prefix/foo", root)

    @transform(assets=["prefix/bar"])
    def bar(context, foo: Annotated[DataFrame, Upstream(asset="prefix/foo")]) -> TransformResult:
        return TransformResult.asset("prefix/bar", foo)

    # Convert transforms to asset specs

    # Test the multi_asset
    storage = InMemoryStorageIO()
    with mount_transform_graph([root, foo, bar], storage) as graph:
        # Execute transforms
        root_result = graph.execute_transform(root)
        foo_result = graph.execute_transform(foo)
        bar_result = graph.execute_transform(bar)

        # Verify outputs
        assert "prefix/root" in root_result.assets
        assert "prefix/foo" in foo_result.assets
        assert "prefix/bar" in bar_result.assets
        assert isinstance(storage.load("prefix/root"), DataFrame)
        assert isinstance(storage.load("prefix/foo"), DataFrame)
        assert isinstance(storage.load("prefix/bar"), DataFrame)


def test_build_single_transform() -> None:
    @transform(assets=["prefix/foo"])
    def foo(
        context, upstream: Annotated[DataFrame, Upstream(asset="prefix/root")]
    ) -> TransformResult:
        return TransformResult.asset("prefix/foo", DataFrame())

    defs = build_inprocess_transform_defs([foo], InMemoryStorageIO())

    assert len(list(defs.assets or [])) == 1
    assets_def = next(iter(defs.assets or []))
    assert isinstance(assets_def, AssetsDefinition)
    assert assets_def.key == AssetKey.from_user_string("prefix/foo")
