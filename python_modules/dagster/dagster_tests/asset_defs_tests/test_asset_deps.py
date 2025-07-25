import dagster as dg
import pytest
from dagster._check import ParameterCheckError
from dagster._core.definitions.assets.definition.asset_dep import AssetDep
from dagster._core.definitions.assets.definition.asset_spec import (
    SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET,
)
from dagster._core.types.dagster_type import DagsterTypeKind

### Tests for AssetDep


def test_basic_instantiation():
    @dg.asset
    def upstream():
        pass

    assert dg.AssetDep("upstream").asset_key == upstream.key
    assert dg.AssetDep(upstream).asset_key == upstream.key
    assert dg.AssetDep(dg.AssetKey(["upstream"])).asset_key == upstream.key

    partition_mapping = dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)

    assert (
        dg.AssetDep("upstream", partition_mapping=partition_mapping).partition_mapping
        == partition_mapping
    )

    # test SourceAsset
    the_source = dg.SourceAsset(key="the_source")
    assert dg.AssetDep(the_source).asset_key == the_source.key


def test_instantiation_with_asset_dep():
    partition_mapping = dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)
    og_dep = dg.AssetDep("upstream", partition_mapping=partition_mapping)

    with pytest.raises(ParameterCheckError):
        assert dg.AssetDep(og_dep) == dg.AssetDep("upstream")  # pyright: ignore[reportArgumentType]


def test_multi_asset_errors():
    @dg.multi_asset(specs=[dg.AssetSpec("asset_1"), dg.AssetSpec("asset_2")])
    def a_multi_asset():
        pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Cannot create an AssetDep from a multi_asset AssetsDefinition",
    ):
        dg.AssetDep(a_multi_asset)


def test_from_coercible():
    # basic coercion
    compare_dep = dg.AssetDep("upstream")

    @dg.asset
    def upstream():
        pass

    assert AssetDep.from_coercible(upstream) == compare_dep
    assert AssetDep.from_coercible("upstream") == compare_dep
    assert AssetDep.from_coercible(dg.AssetKey(["upstream"])) == compare_dep
    assert AssetDep.from_coercible(compare_dep) == compare_dep

    # SourceAsset coercion
    the_source = dg.SourceAsset(key="the_source")
    source_compare_dep = dg.AssetDep(the_source)
    assert AssetDep.from_coercible(the_source) == source_compare_dep

    # partition_mapping should be retained when using from_coercible
    partition_mapping = dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)
    with_partition_mapping = dg.AssetDep(
        "with_partition_mapping", partition_mapping=partition_mapping
    )
    assert AssetDep.from_coercible(with_partition_mapping) == with_partition_mapping

    # multi_assets cannot be coerced by Definition
    @dg.multi_asset(specs=[dg.AssetSpec("asset_1"), dg.AssetSpec("asset_2")])
    def a_multi_asset():
        pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Cannot create an AssetDep from a multi_asset AssetsDefinition",
    ):
        AssetDep.from_coercible(a_multi_asset)

    # Test bad type
    with pytest.raises(ParameterCheckError, match='Param "asset" is not one of'):
        # full error msg: Param "asset" is not one of ['AssetKey', 'AssetSpec', 'AssetsDefinition', 'SourceAsset', 'str']. Got 1 which is type <class 'int'>.
        AssetDep.from_coercible(1)  # pyright: ignore[reportArgumentType]


### Tests for deps parameter on @asset and @multi_asset


class TestingIOManager(dg.IOManager):
    def handle_output(self, context, obj):
        return None

    def load_input(self, context):
        # we should be bypassing the IO Manager, so fail if try to load an input
        assert False


def test_single_asset_deps_via_asset_dep():
    @dg.asset
    def asset_1():
        return None

    @dg.asset(deps=[dg.AssetDep(asset_1)])
    def asset_2():
        return None

    assert len(asset_2.input_names) == 1  # pyright: ignore[reportArgumentType]
    assert asset_2.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = dg.materialize([asset_1, asset_2], resources={"io_manager": TestingIOManager()})

    assert res.success


def test_single_asset_deps_via_assets_definition():
    @dg.asset
    def asset_1():
        return None

    @dg.asset(deps=[asset_1])
    def asset_2():
        return None

    assert len(asset_2.input_names) == 1  # pyright: ignore[reportArgumentType]
    assert asset_2.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = dg.materialize([asset_1, asset_2], resources={"io_manager": TestingIOManager()})

    assert res.success


def test_single_asset_deps_via_string():
    @dg.asset
    def asset_1():
        return None

    @dg.asset(deps=["asset_1"])
    def asset_2():
        return None

    assert len(asset_2.input_names) == 1  # pyright: ignore[reportArgumentType]
    assert asset_2.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = dg.materialize([asset_1, asset_2], resources={"io_manager": TestingIOManager()})

    assert res.success


def test_single_asset_deps_via_asset_key():
    @dg.asset
    def asset_1():
        return None

    @dg.asset(deps=[dg.AssetKey("asset_1")])
    def asset_2():
        return None

    assert len(asset_2.input_names) == 1  # pyright: ignore[reportArgumentType]
    assert asset_2.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = dg.materialize([asset_1, asset_2], resources={"io_manager": TestingIOManager()})
    assert res.success


def test_single_asset_deps_via_mixed_types():
    @dg.asset
    def via_definition():
        return None

    @dg.asset
    def via_string():
        return None

    @dg.asset
    def via_asset_key():
        return None

    @dg.asset(deps=[via_definition, "via_string", dg.AssetKey("via_asset_key")])
    def downstream():
        return None

    assert len(downstream.input_names) == 3  # pyright: ignore[reportArgumentType]
    assert downstream.op.ins["via_definition"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]
    assert downstream.op.ins["via_string"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]
    assert downstream.op.ins["via_asset_key"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = dg.materialize(
        [via_definition, via_string, via_asset_key, downstream],
        resources={"io_manager": TestingIOManager()},
    )
    assert res.success


def test_multi_asset_deps_via_string():
    @dg.multi_asset(
        outs={
            "asset_1": dg.AssetOut(),
            "asset_2": dg.AssetOut(),
        }
    )
    def a_multi_asset():
        return None, None

    @dg.asset(deps=["asset_1"])
    def depends_on_one_sub_asset():
        return None

    assert len(depends_on_one_sub_asset.input_names) == 1  # pyright: ignore[reportArgumentType]
    assert depends_on_one_sub_asset.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    @dg.asset(deps=["asset_1", "asset_2"])
    def depends_on_both_sub_assets():
        return None

    assert len(depends_on_both_sub_assets.input_names) == 2  # pyright: ignore[reportArgumentType]
    assert depends_on_both_sub_assets.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]
    assert depends_on_both_sub_assets.op.ins["asset_2"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = dg.materialize(
        [a_multi_asset, depends_on_one_sub_asset, depends_on_both_sub_assets],
        resources={"io_manager": TestingIOManager()},
    )
    assert res.success


def test_multi_asset_deps_via_key():
    @dg.multi_asset(
        outs={
            "asset_1": dg.AssetOut(),
            "asset_2": dg.AssetOut(),
        }
    )
    def a_multi_asset():
        return None, None

    @dg.asset(deps=[dg.AssetKey("asset_1")])
    def depends_on_one_sub_asset():
        return None

    assert len(depends_on_one_sub_asset.input_names) == 1  # pyright: ignore[reportArgumentType]
    assert depends_on_one_sub_asset.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    @dg.asset(deps=[dg.AssetKey("asset_1"), dg.AssetKey("asset_2")])
    def depends_on_both_sub_assets():
        return None

    assert len(depends_on_both_sub_assets.input_names) == 2  # pyright: ignore[reportArgumentType]
    assert depends_on_both_sub_assets.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]
    assert depends_on_both_sub_assets.op.ins["asset_2"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = dg.materialize(
        [a_multi_asset, depends_on_one_sub_asset, depends_on_both_sub_assets],
        resources={"io_manager": TestingIOManager()},
    )
    assert res.success


def test_multi_asset_deps_via_mixed_types():
    @dg.multi_asset(
        outs={
            "asset_1": dg.AssetOut(),
            "asset_2": dg.AssetOut(),
        }
    )
    def a_multi_asset():
        return None, None

    @dg.asset(deps=[dg.AssetKey("asset_1"), "asset_2"])
    def depends_on_both_sub_assets():
        return None

    assert len(depends_on_both_sub_assets.input_names) == 2  # pyright: ignore[reportArgumentType]
    assert depends_on_both_sub_assets.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]
    assert depends_on_both_sub_assets.op.ins["asset_2"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = dg.materialize(
        [a_multi_asset, depends_on_both_sub_assets], resources={"io_manager": TestingIOManager()}
    )
    assert res.success


def test_multi_asset_deps_with_set():
    @dg.multi_asset(
        outs={
            "asset_1": dg.AssetOut(),
            "asset_2": dg.AssetOut(),
        }
    )
    def a_multi_asset():
        return None, None

    @dg.asset(deps=set(["asset_1", "asset_2"]))
    def depends_on_both_sub_assets():
        return None

    assert len(depends_on_both_sub_assets.input_names) == 2  # pyright: ignore[reportArgumentType]
    assert depends_on_both_sub_assets.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]
    assert depends_on_both_sub_assets.op.ins["asset_2"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = dg.materialize(
        [a_multi_asset, depends_on_both_sub_assets], resources={"io_manager": TestingIOManager()}
    )
    assert res.success


def test_multi_asset_deps_via_assets_definition():
    @dg.multi_asset(
        outs={
            "asset_1": dg.AssetOut(),
            "asset_2": dg.AssetOut(),
        }
    )
    def a_multi_asset():
        return None, None

    @dg.asset(deps=[a_multi_asset])
    def depends_on_both_sub_assets():
        return None

    assert len(depends_on_both_sub_assets.input_names) == 2  # pyright: ignore[reportArgumentType]
    assert depends_on_both_sub_assets.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]
    assert depends_on_both_sub_assets.op.ins["asset_2"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = dg.materialize(
        [a_multi_asset, depends_on_both_sub_assets], resources={"io_manager": TestingIOManager()}
    )
    assert res.success


def test_multi_asset_downstream_deps_via_assets_definition():
    @dg.asset
    def asset_1():
        return None

    @dg.multi_asset(deps=[asset_1], outs={"out1": dg.AssetOut(), "out2": dg.AssetOut()})
    def asset_2():
        return None, None

    assert len(asset_2.input_names) == 1  # pyright: ignore[reportArgumentType]
    assert asset_2.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = dg.materialize([asset_1, asset_2], resources={"io_manager": TestingIOManager()})

    assert res.success


def test_multi_asset_downstream_deps_via_string():
    @dg.asset
    def asset_1():
        return None

    @dg.multi_asset(deps=["asset_1"], outs={"out1": dg.AssetOut(), "out2": dg.AssetOut()})
    def asset_2():
        return None, None

    assert len(asset_2.input_names) == 1  # pyright: ignore[reportArgumentType]
    assert asset_2.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = dg.materialize([asset_1, asset_2], resources={"io_manager": TestingIOManager()})

    assert res.success


def test_multi_asset_downstream_deps_via_asset_key():
    @dg.asset
    def asset_1():
        return None

    @dg.multi_asset(
        deps=[dg.AssetKey("asset_1")], outs={"out1": dg.AssetOut(), "out2": dg.AssetOut()}
    )
    def asset_2():
        return None, None

    assert len(asset_2.input_names) == 1  # pyright: ignore[reportArgumentType]
    assert asset_2.op.ins["asset_1"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = dg.materialize([asset_1, asset_2], resources={"io_manager": TestingIOManager()})
    assert res.success


def test_multi_asset_downstream_deps_via_mixed_types():
    @dg.asset
    def via_definition():
        return None

    @dg.asset
    def via_string():
        return None

    @dg.asset
    def via_asset_key():
        return None

    @dg.multi_asset(
        deps=[via_definition, "via_string", dg.AssetKey("via_asset_key")],
        outs={"out1": dg.AssetOut(), "out2": dg.AssetOut()},
    )
    def downstream():
        return None, None

    assert len(downstream.input_names) == 3  # pyright: ignore[reportArgumentType]
    assert downstream.op.ins["via_definition"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]
    assert downstream.op.ins["via_string"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]
    assert downstream.op.ins["via_asset_key"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = dg.materialize(
        [via_definition, via_string, via_asset_key, downstream],
        resources={"io_manager": TestingIOManager()},
    )
    assert res.success


def test_source_asset_deps_via_assets_definition():
    a_source_asset = dg.SourceAsset("a_key")

    @dg.asset(deps=[a_source_asset])
    def depends_on_source_asset():
        return None

    assert len(depends_on_source_asset.input_names) == 1  # pyright: ignore[reportArgumentType]
    assert depends_on_source_asset.op.ins["a_key"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = dg.materialize([depends_on_source_asset], resources={"io_manager": TestingIOManager()})
    assert res.success


def test_source_asset_deps_via_string():
    a_source_asset = dg.SourceAsset("a_key")  # noqa: F841

    @dg.asset(deps=["a_key"])
    def depends_on_source_asset():
        return None

    assert len(depends_on_source_asset.input_names) == 1  # pyright: ignore[reportArgumentType]
    assert depends_on_source_asset.op.ins["a_key"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = dg.materialize([depends_on_source_asset], resources={"io_manager": TestingIOManager()})
    assert res.success


def test_source_asset_deps_via_key():
    a_source_asset = dg.SourceAsset("a_key")  # noqa: F841

    @dg.asset(deps=[dg.AssetKey("a_key")])
    def depends_on_source_asset():
        return None

    assert len(depends_on_source_asset.input_names) == 1  # pyright: ignore[reportArgumentType]
    assert depends_on_source_asset.op.ins["a_key"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = dg.materialize([depends_on_source_asset], resources={"io_manager": TestingIOManager()})
    assert res.success


def test_interop():
    @dg.asset
    def no_value_asset():
        return None

    @dg.asset(io_manager_key="fs_io_manager")
    def value_asset() -> int:
        return 1

    @dg.asset(
        deps=[no_value_asset],
    )
    def interop_asset(value_asset: int):
        assert value_asset == 1

    assert len(interop_asset.input_names) == 2  # pyright: ignore[reportArgumentType]
    assert interop_asset.op.ins["no_value_asset"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]
    assert interop_asset.op.ins["value_asset"].dagster_type.kind == DagsterTypeKind.SCALAR  # pyright: ignore[reportAttributeAccessIssue]

    res = dg.materialize(
        [no_value_asset, value_asset, interop_asset],
        resources={"io_manager": TestingIOManager(), "fs_io_manager": dg.FilesystemIOManager()},
    )
    assert res.success


def test_non_existent_asset_key():
    @dg.asset(deps=["not_real"])
    def my_asset():
        return None

    res = dg.materialize([my_asset], resources={"io_manager": TestingIOManager()})

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

        @dg.asset(deps=[not_an_asset])  # pyright: ignore[reportArgumentType]
        def my_asset():
            return None


def test_dep_via_deps_and_fn():
    """Test combining deps and ins in the same @asset-decorated function."""

    @dg.asset
    def the_upstream_asset():
        return 1

    # When deps and ins are both set, expect that deps is only used for the asset key and potentially input name.
    for param_dict in [
        {"partition_mapping": dg.IdentityPartitionMapping()},
        {"metadata": {"foo": "bar"}},
        {"key_prefix": "prefix"},
        {"dagster_type": dg.Nothing},
    ]:
        with pytest.raises(dg.DagsterInvalidDefinitionError):

            @dg.asset(
                deps=[dg.AssetDep(the_upstream_asset)],
                ins={"the_upstream_asset": dg.AssetIn(**param_dict)},
            )
            def _(the_upstream_asset):
                return None

    # We allow the asset key to be set via deps and ins as long as no additional information is set.
    @dg.asset(deps=[the_upstream_asset])
    def depends_on_upstream_asset_implicit_remap(the_upstream_asset):
        assert the_upstream_asset == 1

    @dg.asset(
        deps=[dg.AssetDep(the_upstream_asset)],
        ins={"remapped": dg.AssetIn(key=the_upstream_asset.key)},
    )
    def depends_on_upstream_asset_explicit_remap(remapped):
        assert remapped == 1

    res = dg.materialize(
        [
            the_upstream_asset,
            depends_on_upstream_asset_implicit_remap,
            depends_on_upstream_asset_explicit_remap,
        ],
    )
    assert res.success

    @dg.asset
    def upstream2():
        return 2

    # As an unfortunate consequence of the many iterations of dependency specification and the fact that they were all additive with each other,
    # we have to support the case where deps are specified separately in both the function signature and the decorator.
    # This is not recommended, but it is supported.
    @dg.asset(deps=[the_upstream_asset])
    def some_explicit_and_implicit_deps(the_upstream_asset, upstream2):
        assert the_upstream_asset == 1
        assert upstream2 == 2

    @dg.asset(deps=[the_upstream_asset], ins={"remapped": dg.AssetIn(key=upstream2.key)})
    def deps_disjoint_between_args(the_upstream_asset, remapped):
        assert the_upstream_asset == 1
        assert remapped == 2

    res = dg.materialize(
        [
            the_upstream_asset,
            upstream2,
            some_explicit_and_implicit_deps,
            deps_disjoint_between_args,
        ],
    )
    assert res.success


def test_multi_asset_specs_deps_and_fn():
    @dg.asset
    def the_upstream_asset():
        return 1

    # When deps and ins are both set, expect that deps is only used for the asset key and potentially input name.
    for param_dict in [
        {"partition_mapping": dg.IdentityPartitionMapping()},
        {"metadata": {"foo": "bar"}},
        {"key_prefix": "prefix"},
        {"dagster_type": dg.Nothing},
    ]:
        with pytest.raises(dg.DagsterInvalidDefinitionError):

            @dg.multi_asset(
                specs=[dg.AssetSpec("the_asset", deps=[dg.AssetDep(the_upstream_asset)])],
                ins={"the_upstream_asset": dg.AssetIn(**param_dict)},
            )
            def _(the_upstream_asset):
                return None

    # We allow the asset key to be set via deps and ins as long as no additional information is set.
    @dg.multi_asset(specs=[dg.AssetSpec("the_asset", deps=[the_upstream_asset])])
    def depends_on_upstream_asset_implicit_remap(the_upstream_asset):
        assert the_upstream_asset == 1

    @dg.multi_asset(
        specs=[dg.AssetSpec("other_asset", deps=[dg.AssetDep(the_upstream_asset)])],
        ins={"remapped": dg.AssetIn(key=the_upstream_asset.key)},
    )
    def depends_on_upstream_asset_explicit_remap(remapped):
        assert remapped == 1

    res = dg.materialize(
        [
            the_upstream_asset,
            depends_on_upstream_asset_implicit_remap,
            depends_on_upstream_asset_explicit_remap,
        ],
    )
    assert res.success

    # We do not allow you to set a dependency purely via input if you're opting in to the spec pattern.
    with pytest.raises(dg.DagsterInvalidDefinitionError):

        @dg.multi_asset(
            specs=[dg.AssetSpec("the_asset")],
        )
        def _(the_upstream_asset):
            return None


def test_allow_remapping_io_manager_key() -> None:
    @dg.asset
    def the_upstream_asset():
        return 1

    @dg.asset(
        deps=[the_upstream_asset],
        ins={"the_upstream_asset": dg.AssetIn(input_manager_key="custom_io")},
    )
    def depends_on_upstream_asset(the_upstream_asset):
        assert the_upstream_asset == 1

    calls = []

    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            raise Exception("Should not be called")

        def load_input(self, context):
            calls.append("load_input")
            return 1

    res = dg.materialize(
        [the_upstream_asset, depends_on_upstream_asset],
        resources={"custom_io": MyIOManager()},
    )
    assert res.success
    assert calls == ["load_input"]


def test_duplicate_deps():
    @dg.asset
    def the_upstream_asset():
        return None

    @dg.asset(deps=[the_upstream_asset, the_upstream_asset])
    def the_downstream_asset():
        return None

    assert len(the_downstream_asset.input_names) == 1  # pyright: ignore[reportArgumentType]
    assert the_downstream_asset.op.ins["the_upstream_asset"].dagster_type.is_nothing  # pyright: ignore[reportAttributeAccessIssue]

    res = dg.materialize(
        [the_downstream_asset, the_upstream_asset],
        resources={"io_manager": TestingIOManager(), "fs_io_manager": dg.FilesystemIOManager()},
    )
    assert res.success

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match=r"Cannot set a dependency on asset .* more than once",
    ):

        @dg.asset(
            deps=[
                the_upstream_asset,
                dg.AssetDep(
                    asset=the_upstream_asset,
                    partition_mapping=dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
                ),
            ]
        )
        def conflicting_deps():
            return None


def test_nonexistent_deps_creates_stub_asset():
    does_not_exist = dg.AssetKey(["does_not_exist"])

    @dg.asset(deps=[does_not_exist])
    def the_asset():
        return None

    defs = dg.Definitions(assets=[the_asset])

    asset_graph = defs.resolve_asset_graph()

    assert asset_graph.get(the_asset.key).is_materializable
    assert not asset_graph.get(does_not_exist).is_materializable
    assert (
        asset_graph.get(does_not_exist).metadata[SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET]
        is True
    )


def test_nonexistent_asset_check_deps_creates_stub_asset():
    does_not_exist = dg.AssetKey(["does_not_exist"])

    @dg.asset_check(asset=does_not_exist)
    def the_asset_check():
        return dg.AssetCheckResult(
            passed=False,
        )

    defs = dg.Definitions(asset_checks=[the_asset_check])

    asset_graph = defs.resolve_asset_graph()

    assert not asset_graph.get(does_not_exist).is_materializable
    assert (
        asset_graph.get(does_not_exist).metadata[SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET]
        is True
    )
