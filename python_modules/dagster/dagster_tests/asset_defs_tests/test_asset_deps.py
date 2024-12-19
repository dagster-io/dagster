import pytest
from dagster import (
    AssetKey,
    AssetOut,
    FilesystemIOManager,
    IOManager,
    Nothing,
    SourceAsset,
    TimeWindowPartitionMapping,
    asset,
    materialize,
    multi_asset,
)
from dagster._check import ParameterCheckError
from dagster._core.definitions.asset_dep import AssetDep
from dagster._core.definitions.asset_in import AssetIn
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.partition_mapping import IdentityPartitionMapping
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster._core.types.dagster_type import DagsterTypeKind

### Tests for AssetDep


def test_basic_instantiation():
    @asset
    def upstream():
        pass

    assert AssetDep("upstream").asset_key == upstream.key
    assert AssetDep(upstream).asset_key == upstream.key
    assert AssetDep(AssetKey(["upstream"])).asset_key == upstream.key

    partition_mapping = TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)

    assert (
        AssetDep("upstream", partition_mapping=partition_mapping).partition_mapping
        == partition_mapping
    )

    # test SourceAsset
    the_source = SourceAsset(key="the_source")
    assert AssetDep(the_source).asset_key == the_source.key


def test_instantiation_with_asset_dep():
    partition_mapping = TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)
    og_dep = AssetDep("upstream", partition_mapping=partition_mapping)

    with pytest.raises(ParameterCheckError):
        assert AssetDep(og_dep) == AssetDep("upstream")  # pyright: ignore[reportArgumentType]


def test_multi_asset_errors():
    @multi_asset(specs=[AssetSpec("asset_1"), AssetSpec("asset_2")])
    def a_multi_asset():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Cannot create an AssetDep from a multi_asset AssetsDefinition",
    ):
        AssetDep(a_multi_asset)


def test_from_coercible():
    # basic coercion
    compare_dep = AssetDep("upstream")

    @asset
    def upstream():
        pass

    assert AssetDep.from_coercible(upstream) == compare_dep
    assert AssetDep.from_coercible("upstream") == compare_dep
    assert AssetDep.from_coercible(AssetKey(["upstream"])) == compare_dep
    assert AssetDep.from_coercible(compare_dep) == compare_dep

    # SourceAsset coercion
    the_source = SourceAsset(key="the_source")
    source_compare_dep = AssetDep(the_source)
    assert AssetDep.from_coercible(the_source) == source_compare_dep

    # partition_mapping should be retained when using from_coercible
    partition_mapping = TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)
    with_partition_mapping = AssetDep("with_partition_mapping", partition_mapping=partition_mapping)
    assert AssetDep.from_coercible(with_partition_mapping) == with_partition_mapping

    # multi_assets cannot be coerced by Definition
    @multi_asset(specs=[AssetSpec("asset_1"), AssetSpec("asset_2")])
    def a_multi_asset():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Cannot create an AssetDep from a multi_asset AssetsDefinition",
    ):
        AssetDep.from_coercible(a_multi_asset)

    # Test bad type
    with pytest.raises(ParameterCheckError, match='Param "asset" is not one of'):
        # full error msg: Param "asset" is not one of ['AssetKey', 'AssetSpec', 'AssetsDefinition', 'SourceAsset', 'str']. Got 1 which is type <class 'int'>.
        AssetDep.from_coercible(1)  # pyright: ignore[reportArgumentType]


### Tests for deps parameter on @asset and @multi_asset


class TestingIOManager(IOManager):
    def handle_output(self, context, obj):
        return None

    def load_input(self, context):
        # we should be bypassing the IO Manager, so fail if try to load an input
        assert False


def test_single_asset_deps_via_asset_dep():
    @asset
    def asset_1():
        return None

    @asset(deps=[AssetDep(asset_1)])
    def asset_2():
        return None

    assert len(asset_2.input_names) == 1  # pyright: ignore[reportArgumentType]
    assert asset_2.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = materialize([asset_1, asset_2], resources={"io_manager": TestingIOManager()})

    assert res.success


def test_single_asset_deps_via_assets_definition():
    @asset
    def asset_1():
        return None

    @asset(deps=[asset_1])
    def asset_2():
        return None

    assert len(asset_2.input_names) == 1  # pyright: ignore[reportArgumentType]
    assert asset_2.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = materialize([asset_1, asset_2], resources={"io_manager": TestingIOManager()})

    assert res.success


def test_single_asset_deps_via_string():
    @asset
    def asset_1():
        return None

    @asset(deps=["asset_1"])
    def asset_2():
        return None

    assert len(asset_2.input_names) == 1  # pyright: ignore[reportArgumentType]
    assert asset_2.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = materialize([asset_1, asset_2], resources={"io_manager": TestingIOManager()})

    assert res.success


def test_single_asset_deps_via_asset_key():
    @asset
    def asset_1():
        return None

    @asset(deps=[AssetKey("asset_1")])
    def asset_2():
        return None

    assert len(asset_2.input_names) == 1  # pyright: ignore[reportArgumentType]
    assert asset_2.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = materialize([asset_1, asset_2], resources={"io_manager": TestingIOManager()})
    assert res.success


def test_single_asset_deps_via_mixed_types():
    @asset
    def via_definition():
        return None

    @asset
    def via_string():
        return None

    @asset
    def via_asset_key():
        return None

    @asset(deps=[via_definition, "via_string", AssetKey("via_asset_key")])
    def downstream():
        return None

    assert len(downstream.input_names) == 3  # pyright: ignore[reportArgumentType]
    assert downstream.op.ins["via_definition"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]
    assert downstream.op.ins["via_string"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]
    assert downstream.op.ins["via_asset_key"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = materialize(
        [via_definition, via_string, via_asset_key, downstream],
        resources={"io_manager": TestingIOManager()},
    )
    assert res.success


def test_multi_asset_deps_via_string():
    @multi_asset(
        outs={
            "asset_1": AssetOut(),
            "asset_2": AssetOut(),
        }
    )
    def a_multi_asset():
        return None, None

    @asset(deps=["asset_1"])
    def depends_on_one_sub_asset():
        return None

    assert len(depends_on_one_sub_asset.input_names) == 1  # pyright: ignore[reportArgumentType]
    assert depends_on_one_sub_asset.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    @asset(deps=["asset_1", "asset_2"])
    def depends_on_both_sub_assets():
        return None

    assert len(depends_on_both_sub_assets.input_names) == 2  # pyright: ignore[reportArgumentType]
    assert depends_on_both_sub_assets.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]
    assert depends_on_both_sub_assets.op.ins["asset_2"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = materialize(
        [a_multi_asset, depends_on_one_sub_asset, depends_on_both_sub_assets],
        resources={"io_manager": TestingIOManager()},
    )
    assert res.success


def test_multi_asset_deps_via_key():
    @multi_asset(
        outs={
            "asset_1": AssetOut(),
            "asset_2": AssetOut(),
        }
    )
    def a_multi_asset():
        return None, None

    @asset(deps=[AssetKey("asset_1")])
    def depends_on_one_sub_asset():
        return None

    assert len(depends_on_one_sub_asset.input_names) == 1  # pyright: ignore[reportArgumentType]
    assert depends_on_one_sub_asset.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    @asset(deps=[AssetKey("asset_1"), AssetKey("asset_2")])
    def depends_on_both_sub_assets():
        return None

    assert len(depends_on_both_sub_assets.input_names) == 2  # pyright: ignore[reportArgumentType]
    assert depends_on_both_sub_assets.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]
    assert depends_on_both_sub_assets.op.ins["asset_2"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = materialize(
        [a_multi_asset, depends_on_one_sub_asset, depends_on_both_sub_assets],
        resources={"io_manager": TestingIOManager()},
    )
    assert res.success


def test_multi_asset_deps_via_mixed_types():
    @multi_asset(
        outs={
            "asset_1": AssetOut(),
            "asset_2": AssetOut(),
        }
    )
    def a_multi_asset():
        return None, None

    @asset(deps=[AssetKey("asset_1"), "asset_2"])
    def depends_on_both_sub_assets():
        return None

    assert len(depends_on_both_sub_assets.input_names) == 2  # pyright: ignore[reportArgumentType]
    assert depends_on_both_sub_assets.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]
    assert depends_on_both_sub_assets.op.ins["asset_2"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = materialize(
        [a_multi_asset, depends_on_both_sub_assets], resources={"io_manager": TestingIOManager()}
    )
    assert res.success


def test_multi_asset_deps_with_set():
    @multi_asset(
        outs={
            "asset_1": AssetOut(),
            "asset_2": AssetOut(),
        }
    )
    def a_multi_asset():
        return None, None

    @asset(deps=set(["asset_1", "asset_2"]))
    def depends_on_both_sub_assets():
        return None

    assert len(depends_on_both_sub_assets.input_names) == 2  # pyright: ignore[reportArgumentType]
    assert depends_on_both_sub_assets.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]
    assert depends_on_both_sub_assets.op.ins["asset_2"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = materialize(
        [a_multi_asset, depends_on_both_sub_assets], resources={"io_manager": TestingIOManager()}
    )
    assert res.success


def test_multi_asset_deps_via_assets_definition():
    @multi_asset(
        outs={
            "asset_1": AssetOut(),
            "asset_2": AssetOut(),
        }
    )
    def a_multi_asset():
        return None, None

    @asset(deps=[a_multi_asset])
    def depends_on_both_sub_assets():
        return None

    assert len(depends_on_both_sub_assets.input_names) == 2  # pyright: ignore[reportArgumentType]
    assert depends_on_both_sub_assets.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]
    assert depends_on_both_sub_assets.op.ins["asset_2"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = materialize(
        [a_multi_asset, depends_on_both_sub_assets], resources={"io_manager": TestingIOManager()}
    )
    assert res.success


def test_multi_asset_downstream_deps_via_assets_definition():
    @asset
    def asset_1():
        return None

    @multi_asset(deps=[asset_1], outs={"out1": AssetOut(), "out2": AssetOut()})
    def asset_2():
        return None, None

    assert len(asset_2.input_names) == 1  # pyright: ignore[reportArgumentType]
    assert asset_2.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = materialize([asset_1, asset_2], resources={"io_manager": TestingIOManager()})

    assert res.success


def test_multi_asset_downstream_deps_via_string():
    @asset
    def asset_1():
        return None

    @multi_asset(deps=["asset_1"], outs={"out1": AssetOut(), "out2": AssetOut()})
    def asset_2():
        return None, None

    assert len(asset_2.input_names) == 1  # pyright: ignore[reportArgumentType]
    assert asset_2.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = materialize([asset_1, asset_2], resources={"io_manager": TestingIOManager()})

    assert res.success


def test_multi_asset_downstream_deps_via_asset_key():
    @asset
    def asset_1():
        return None

    @multi_asset(deps=[AssetKey("asset_1")], outs={"out1": AssetOut(), "out2": AssetOut()})
    def asset_2():
        return None, None

    assert len(asset_2.input_names) == 1  # pyright: ignore[reportArgumentType]
    assert asset_2.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = materialize([asset_1, asset_2], resources={"io_manager": TestingIOManager()})
    assert res.success


def test_multi_asset_downstream_deps_via_mixed_types():
    @asset
    def via_definition():
        return None

    @asset
    def via_string():
        return None

    @asset
    def via_asset_key():
        return None

    @multi_asset(
        deps=[via_definition, "via_string", AssetKey("via_asset_key")],
        outs={"out1": AssetOut(), "out2": AssetOut()},
    )
    def downstream():
        return None, None

    assert len(downstream.input_names) == 3  # pyright: ignore[reportArgumentType]
    assert downstream.op.ins["via_definition"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]
    assert downstream.op.ins["via_string"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]
    assert downstream.op.ins["via_asset_key"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = materialize(
        [via_definition, via_string, via_asset_key, downstream],
        resources={"io_manager": TestingIOManager()},
    )
    assert res.success


def test_source_asset_deps_via_assets_definition():
    a_source_asset = SourceAsset("a_key")

    @asset(deps=[a_source_asset])
    def depends_on_source_asset():
        return None

    assert len(depends_on_source_asset.input_names) == 1  # pyright: ignore[reportArgumentType]
    assert depends_on_source_asset.op.ins["a_key"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = materialize([depends_on_source_asset], resources={"io_manager": TestingIOManager()})
    assert res.success


def test_source_asset_deps_via_string():
    a_source_asset = SourceAsset("a_key")  # noqa: F841

    @asset(deps=["a_key"])
    def depends_on_source_asset():
        return None

    assert len(depends_on_source_asset.input_names) == 1  # pyright: ignore[reportArgumentType]
    assert depends_on_source_asset.op.ins["a_key"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = materialize([depends_on_source_asset], resources={"io_manager": TestingIOManager()})
    assert res.success


def test_source_asset_deps_via_key():
    a_source_asset = SourceAsset("a_key")  # noqa: F841

    @asset(deps=[AssetKey("a_key")])
    def depends_on_source_asset():
        return None

    assert len(depends_on_source_asset.input_names) == 1  # pyright: ignore[reportArgumentType]
    assert depends_on_source_asset.op.ins["a_key"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = materialize([depends_on_source_asset], resources={"io_manager": TestingIOManager()})
    assert res.success


def test_interop():
    @asset
    def no_value_asset():
        return None

    @asset(io_manager_key="fs_io_manager")
    def value_asset() -> int:
        return 1

    @asset(
        deps=[no_value_asset],
    )
    def interop_asset(value_asset: int):
        assert value_asset == 1

    assert len(interop_asset.input_names) == 2  # pyright: ignore[reportArgumentType]
    assert interop_asset.op.ins["no_value_asset"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]
    assert interop_asset.op.ins["value_asset"].dagster_type.kind == DagsterTypeKind.SCALAR  # pyright: ignore[reportAttributeAccessIssue]

    res = materialize(
        [no_value_asset, value_asset, interop_asset],
        resources={"io_manager": TestingIOManager(), "fs_io_manager": FilesystemIOManager()},
    )
    assert res.success


def test_non_existent_asset_key():
    @asset(deps=["not_real"])
    def my_asset():
        return None

    res = materialize([my_asset], resources={"io_manager": TestingIOManager()})

    assert res.success


def test_bad_types():
    class NotAnAsset:
        def __init__(self):
            self.foo = "bar"

    not_an_asset = NotAnAsset()

    with pytest.raises(
        ParameterCheckError,
        match='Param "asset" is not one of ',
    ):

        @asset(deps=[not_an_asset])  # pyright: ignore[reportArgumentType]
        def my_asset():
            return None


def test_dep_via_deps_and_fn():
    """Test combining deps and ins in the same @asset-decorated function."""

    @asset
    def the_upstream_asset():
        return 1

    # When deps and ins are both set, expect that deps is only used for the asset key and potentially input name.
    for param_dict in [
        {"partition_mapping": IdentityPartitionMapping()},
        {"metadata": {"foo": "bar"}},
        {"key_prefix": "prefix"},
        {"dagster_type": Nothing},
    ]:
        with pytest.raises(DagsterInvalidDefinitionError):

            @asset(
                deps=[AssetDep(the_upstream_asset)],
                ins={"the_upstream_asset": AssetIn(**param_dict)},
            )
            def _(the_upstream_asset):
                return None

    # We allow the asset key to be set via deps and ins as long as no additional information is set.
    @asset(deps=[the_upstream_asset])
    def depends_on_upstream_asset_implicit_remap(the_upstream_asset):
        assert the_upstream_asset == 1

    @asset(
        deps=[AssetDep(the_upstream_asset)], ins={"remapped": AssetIn(key=the_upstream_asset.key)}
    )
    def depends_on_upstream_asset_explicit_remap(remapped):
        assert remapped == 1

    res = materialize(
        [
            the_upstream_asset,
            depends_on_upstream_asset_implicit_remap,
            depends_on_upstream_asset_explicit_remap,
        ],
    )
    assert res.success

    @asset
    def upstream2():
        return 2

    # As an unfortunate consequence of the many iterations of dependency specification and the fact that they were all additive with each other,
    # we have to support the case where deps are specified separately in both the function signature and the decorator.
    # This is not recommended, but it is supported.
    @asset(deps=[the_upstream_asset])
    def some_explicit_and_implicit_deps(the_upstream_asset, upstream2):
        assert the_upstream_asset == 1
        assert upstream2 == 2

    @asset(deps=[the_upstream_asset], ins={"remapped": AssetIn(key=upstream2.key)})
    def deps_disjoint_between_args(the_upstream_asset, remapped):
        assert the_upstream_asset == 1
        assert remapped == 2

    res = materialize(
        [
            the_upstream_asset,
            upstream2,
            some_explicit_and_implicit_deps,
            deps_disjoint_between_args,
        ],
    )
    assert res.success


def test_multi_asset_specs_deps_and_fn():
    @asset
    def the_upstream_asset():
        return 1

    # When deps and ins are both set, expect that deps is only used for the asset key and potentially input name.
    for param_dict in [
        {"partition_mapping": IdentityPartitionMapping()},
        {"metadata": {"foo": "bar"}},
        {"key_prefix": "prefix"},
        {"dagster_type": Nothing},
    ]:
        with pytest.raises(DagsterInvalidDefinitionError):

            @multi_asset(
                specs=[AssetSpec("the_asset", deps=[AssetDep(the_upstream_asset)])],
                ins={"the_upstream_asset": AssetIn(**param_dict)},
            )
            def _(the_upstream_asset):
                return None

    # We allow the asset key to be set via deps and ins as long as no additional information is set.
    @multi_asset(specs=[AssetSpec("the_asset", deps=[the_upstream_asset])])
    def depends_on_upstream_asset_implicit_remap(the_upstream_asset):
        assert the_upstream_asset == 1

    @multi_asset(
        specs=[AssetSpec("other_asset", deps=[AssetDep(the_upstream_asset)])],
        ins={"remapped": AssetIn(key=the_upstream_asset.key)},
    )
    def depends_on_upstream_asset_explicit_remap(remapped):
        assert remapped == 1

    res = materialize(
        [
            the_upstream_asset,
            depends_on_upstream_asset_implicit_remap,
            depends_on_upstream_asset_explicit_remap,
        ],
    )
    assert res.success

    # We do not allow you to set a dependency purely via input if you're opting in to the spec pattern.
    with pytest.raises(DagsterInvalidDefinitionError):

        @multi_asset(
            specs=[AssetSpec("the_asset")],
        )
        def _(the_upstream_asset):
            return None


def test_allow_remapping_io_manager_key() -> None:
    @asset
    def the_upstream_asset():
        return 1

    @asset(
        deps=[the_upstream_asset],
        ins={"the_upstream_asset": AssetIn(input_manager_key="custom_io")},
    )
    def depends_on_upstream_asset(the_upstream_asset):
        assert the_upstream_asset == 1

    calls = []

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            raise Exception("Should not be called")

        def load_input(self, context):
            calls.append("load_input")
            return 1

    res = materialize(
        [the_upstream_asset, depends_on_upstream_asset],
        resources={"custom_io": MyIOManager()},
    )
    assert res.success
    assert calls == ["load_input"]


def test_duplicate_deps():
    @asset
    def the_upstream_asset():
        return None

    @asset(deps=[the_upstream_asset, the_upstream_asset])
    def the_downstream_asset():
        return None

    assert len(the_downstream_asset.input_names) == 1  # pyright: ignore[reportArgumentType]
    assert the_downstream_asset.op.ins["the_upstream_asset"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = materialize(
        [the_downstream_asset, the_upstream_asset],
        resources={"io_manager": TestingIOManager(), "fs_io_manager": FilesystemIOManager()},
    )
    assert res.success

    with pytest.raises(
        DagsterInvariantViolationError, match=r"Cannot set a dependency on asset .* more than once"
    ):

        @asset(
            deps=[
                the_upstream_asset,
                AssetDep(
                    asset=the_upstream_asset,
                    partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
                ),
            ]
        )
        def conflicting_deps():
            return None
