from typing import Annotated

from dagster_pipes.transforms.transform import (
    TestResult,
    TransformContext,
    Upstream,
    get_transform_metadata,
    get_upstream_metadata,
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
    ) -> DataFrame:
        return DataFrame()

    @transform(assets=["prefix/bar"])
    def bar(
        context: TransformContext, foo: Annotated[DataFrame, Upstream(asset="prefix/foo")]
    ) -> DataFrame:
        return DataFrame()

    @transform(checks=["prefix/bar/test_1"])
    def bar_col1_test(
        context: TransformContext, bar: Annotated[DataFrame, Upstream(asset="prefix/bar")]
    ) -> TestResult: ...

    # Test foo transform metadata
    assert hasattr(foo, "__dagster_transforms__")
    foo_metadata = get_transform_metadata(foo)
    assert foo_metadata.assets == ["prefix/foo"]
    assert foo_metadata.checks == []

    # Test bar transform metadata
    assert hasattr(bar, "__dagster_transforms__")
    bar_metadata = get_transform_metadata(bar)
    assert bar_metadata.assets == ["prefix/bar"]
    assert bar_metadata.checks == []

    # # Test bar_col1_test transform metadata
    # assert hasattr(bar_col1_test, "__dagster_transforms__")
    # bar_col1_test_metadata = get_transform_metadata(bar_col1_test)
    # assert bar_col1_test_metadata.assets == []
    # assert bar_col1_test_metadata.checks == ["prefix/bar/test_1"]


def test_upstream_metadata():
    @transform(assets=["prefix/foo"])
    def foo(
        context: TransformContext, root: Annotated[DataFrame, Upstream(asset="prefix/root")]
    ) -> DataFrame:
        return DataFrame()

    @transform(assets=["prefix/bar"])
    def bar(
        context: TransformContext, foo: Annotated[DataFrame, Upstream(asset="prefix/foo")]
    ) -> DataFrame:
        return DataFrame()

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
    ) -> DataFrame:
        return DataFrame()

    @transform(assets=["prefix/bar"])
    def bar(
        context: TransformContext, foo: Annotated[DataFrame, Upstream(asset="prefix/foo")]
    ) -> DataFrame:
        return DataFrame()

    # Test foo execution
    result = foo(TransformContext(), DataFrame())
    assert isinstance(result, DataFrame)

    # Test bar execution
    result = bar(TransformContext(), DataFrame())
    assert isinstance(result, DataFrame)
