from collections import deque
from collections.abc import Callable, Iterable, Sequence

import dagster as dg
import pytest
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.definitions.observe import observe


def test_all_fields():
    dg.StaticPartitionsDefinition(["a", "b", "c", "d"])

    @dg.io_manager(required_resource_keys={"baz"})  # pyright: ignore[reportArgumentType]
    def foo_manager():
        pass

    @dg.observable_source_asset(
        name="alpha",
        description="beta",
        key_prefix="delta",
        metadata={"epsilon": "gamma"},
        io_manager_key="lambda",
        io_manager_def=foo_manager,
        group_name="rho",
        auto_observe_interval_minutes=5,
    )
    def foo_source_asset(context):
        raise Exception("not executed")

    assert foo_source_asset.key == dg.AssetKey(["delta", "alpha"])
    assert foo_source_asset.description == "beta"
    assert foo_source_asset.io_manager_key == "lambda"
    assert foo_source_asset.group_name == "rho"
    assert foo_source_asset.resource_defs == {"lambda": foo_manager}
    assert foo_source_asset.io_manager_def == foo_manager
    assert foo_source_asset.metadata == {"epsilon": MetadataValue.text("gamma")}
    assert foo_source_asset.auto_observe_interval_minutes == 5


def test_no_context_observable_asset():
    executed = {}

    @dg.observable_source_asset
    def observable_asset_no_context():
        executed["yes"] = True
        return dg.DataVersion("version-string")

    result = observe([observable_asset_no_context])
    assert result.success
    assert executed["yes"]


def test_key_and_name_args():
    @dg.observable_source_asset(key=["apple", "banana"])
    def key_specified(): ...

    assert key_specified.key == dg.AssetKey(["apple", "banana"])
    assert key_specified.op.name == "apple__banana"

    @dg.observable_source_asset(key_prefix=["apple", "banana"])
    def key_prefix_specified(): ...

    assert key_prefix_specified.key == dg.AssetKey(["apple", "banana", "key_prefix_specified"])
    assert key_prefix_specified.op.name == "apple__banana__key_prefix_specified"

    @dg.observable_source_asset(name="peach")
    def name_specified(): ...

    assert name_specified.key == dg.AssetKey(["peach"])
    assert name_specified.op.name == "peach"

    @dg.observable_source_asset(key_prefix=["apple", "banana"], name="peach")
    def key_prefix_and_name_specified(): ...

    assert key_prefix_and_name_specified.key == dg.AssetKey(["apple", "banana", "peach"])
    assert key_prefix_and_name_specified.op.name == "apple__banana__peach"

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Cannot specify a name or key prefix for @observable_source_asset when the key argument is provided",
    ):

        @dg.observable_source_asset(key_prefix=["apple", "banana"], key=["peach", "nectarine"])
        def key_prefix_and_key_specified(): ...

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Cannot specify a name or key prefix for @observable_source_asset when the key argument is provided",
    ):

        @dg.observable_source_asset(name=["peach"], key=["peach", "nectarine"])  # pyright: ignore[reportArgumentType]
        def name_and_key_specified(): ...


def test_op_tags():
    tags = {"foo": "bar"}

    @dg.observable_source_asset(op_tags=tags)
    def op_tags_specified(): ...

    assert op_tags_specified.op.tags == tags


def test_tags():
    tags = {"foo": "bar"}

    @dg.observable_source_asset(tags=tags)
    def asset1(): ...

    assert asset1.tags == tags

    with pytest.raises(dg.DagsterInvalidDefinitionError, match="Found invalid tag keys"):

        @dg.observable_source_asset(tags={"a%": "b"})
        def asset1(): ...


def test_multi_observable_source_asset_tags():
    tags = {"foo": "bar"}

    @dg.multi_observable_source_asset(specs=[dg.AssetSpec("asset1", tags=tags)])
    def assets(): ...

    assert assets.tags_by_key[dg.AssetKey("asset1")] == tags

    with pytest.raises(dg.DagsterInvalidDefinitionError, match="Found invalid tag keys"):

        @dg.multi_observable_source_asset(specs=[dg.AssetSpec("asset1", tags={"a%": "b"})])
        def assets(): ...


@pytest.mark.parametrize("sequence_factory", [list, tuple, deque])
def test_multi_observable_source_sequence_specs(
    sequence_factory: Callable[[Iterable[dg.AssetSpec]], Sequence[dg.AssetSpec]],
):
    specs = [dg.AssetSpec("asset1", group_name="group1")]
    sequence_specs = sequence_factory(specs)

    @dg.multi_observable_source_asset(specs=sequence_specs)
    def assets(): ...

    assert list(assets.specs) == list(sequence_specs)


def test_op_tags_forwarded_to_execution_step() -> None:
    op_tags = {"foo": "bar", "baz": "qux"}

    @dg.observable_source_asset(op_tags=op_tags)
    def tagged_source_asset():
        return dg.DataVersion("1")

    # Create a job that includes the source asset
    defs = dg.Definitions(assets=[tagged_source_asset])
    global_job = defs.resolve_implicit_global_asset_job_def()
    assert len(global_job.nodes) == 1
    assert global_job.nodes[0].tags == op_tags
