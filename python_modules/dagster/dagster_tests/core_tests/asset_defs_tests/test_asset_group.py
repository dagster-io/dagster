import pytest

from dagster import (
    AssetKey,
    DagsterInvalidDefinitionError,
    IOManager,
    Out,
    fs_asset_io_manager,
    in_process_executor,
    io_manager,
    mem_io_manager,
    repository,
    resource,
)
from dagster.core.asset_defs import AssetGroup, AssetIn, SourceAsset, asset, multi_asset


def test_asset_group_from_list():
    @asset
    def asset_foo():
        return "foo"

    @asset
    def asset_bar():
        return "bar"

    @asset(ins={"asset_bar": AssetIn(asset_key=AssetKey("asset_foo"))})
    def last_asset(asset_bar):
        return asset_bar

    group = AssetGroup(assets=[asset_foo, asset_bar, last_asset])

    @repository
    def the_repo():
        return [group]

    assert len(the_repo.get_all_jobs()) == 1
    asset_group_underlying_job = the_repo.get_all_jobs()[0]
    assert asset_group_underlying_job.name == group.all_assets_job_name

    result = asset_group_underlying_job.execute_in_process()
    assert result.success


def test_asset_group_source_asset():
    foo_fa = SourceAsset(key=AssetKey("foo"), io_manager_key="the_manager")

    @asset
    def asset_depends_on_source(foo):
        return foo

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            return 5

    @io_manager
    def the_manager():
        return MyIOManager()

    group = AssetGroup(
        assets=[asset_depends_on_source],
        source_assets=[foo_fa],
        resource_defs={"the_manager": the_manager},
    )

    @repository
    def the_repo():
        return [group]

    asset_group_underlying_job = the_repo.get_all_jobs()[0]
    assert asset_group_underlying_job.name == group.all_assets_job_name

    result = asset_group_underlying_job.execute_in_process()
    assert result.success


def test_asset_group_with_resources():
    @asset(required_resource_keys={"foo"})
    def asset_foo(context):
        return context.resources.foo

    @resource
    def the_resource():
        return "foo"

    group = AssetGroup([asset_foo], resource_defs={"foo": the_resource})

    @repository
    def the_repo():
        return [group]

    asset_group_underlying_job = the_repo.get_all_jobs()[0]
    assert asset_group_underlying_job.name == group.all_assets_job_name

    result = asset_group_underlying_job.execute_in_process()
    assert result.success
    assert result.output_for_node("asset_foo") == "foo"


def test_asset_group_missing_resources():
    @asset(required_resource_keys={"foo"})
    def asset_foo(context):
        return context.resources.foo

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=r"AssetGroup is missing required resource keys for asset 'asset_foo'. Missing resource keys: \['foo'\]",
    ):
        AssetGroup([asset_foo])

    source_asset_io_req = SourceAsset(key=AssetKey("foo"), io_manager_key="foo")

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=r"SourceAsset with key AssetKey\(\['foo'\]\) requires io manager with key 'foo', which was not provided on AssetGroup. Provided keys: \['io_manager', 'root_manager'\]",
    ):
        AssetGroup([], source_assets=[source_asset_io_req])


def test_asset_group_with_executor():
    @asset
    def the_asset():
        pass

    @repository
    def the_repo():
        return [AssetGroup([the_asset], executor_def=in_process_executor)]

    asset_group_underlying_job = the_repo.get_all_jobs()[0]
    assert (
        asset_group_underlying_job.executor_def  # pylint: disable=comparison-with-callable
        == in_process_executor
    )


def test_asset_group_requires_root_manager():
    @asset(io_manager_key="blah")
    def asset_foo():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=r"Output 'result' with AssetKey 'AssetKey\(\['asset_foo'\]\)' "
        r"requires io manager 'blah' but was not provided on asset group. "
        r"Provided resources: \['io_manager', 'root_manager'\]",
    ):
        AssetGroup([asset_foo])


def test_resource_override():
    @resource
    def the_resource():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Resource dictionary included resource with key 'root_manager', "
        "which is a reserved resource keyword in Dagster. Please change this "
        "key, and then change all places that require this key to a new value.",
    ):
        AssetGroup([], resource_defs={"root_manager": the_resource})

    @repository
    def the_repo():
        return [AssetGroup([], resource_defs={"io_manager": mem_io_manager})]

    asset_group_underlying_job = the_repo.get_all_jobs()[0]
    assert (  # pylint: disable=comparison-with-callable
        asset_group_underlying_job.resource_defs["io_manager"] == mem_io_manager
    )


def asset_aware_io_manager():
    class MyIOManager(IOManager):
        def __init__(self):
            self.db = {}

        def handle_output(self, context, obj):
            self.db[context.asset_key] = obj

        def load_input(self, context):
            return self.db.get(context.asset_key)

    io_manager_obj = MyIOManager()

    @io_manager
    def _asset_aware():
        return io_manager_obj

    return io_manager_obj, _asset_aware


def test_asset_group_build_subset_job():
    @asset
    def start_asset():
        return "foo"

    @multi_asset(outs={"o1": Out(asset_key=AssetKey("o1")), "o2": Out(asset_key=AssetKey("o2"))})
    def middle_asset(start_asset):
        return (start_asset, start_asset)

    @asset
    def follows_o1(o1):
        return o1

    @asset
    def follows_o2(o2):
        return o2

    _, io_manager_def = asset_aware_io_manager()
    group = AssetGroup(
        [start_asset, middle_asset, follows_o1, follows_o2],
        resource_defs={"io_manager": io_manager_def},
    )

    full_job = group.build_job("full", selection="*")

    result = full_job.execute_in_process()

    assert result.success
    assert result.output_for_node("follows_o1") == "foo"
    assert result.output_for_node("follows_o2") == "foo"

    test_single = group.build_job(name="test_single", selection="follows_o2")
    assert len(test_single.all_node_defs) == 1
    assert test_single.all_node_defs[0].name == "follows_o2"

    result = test_single.execute_in_process()
    assert result.success
    assert result.output_for_node("follows_o2") == "foo"

    test_up_star = group.build_job(name="test_up_star", selection="*follows_o2")
    assert len(test_up_star.all_node_defs) == 3
    assert set([node.name for node in test_up_star.all_node_defs]) == {
        "follows_o2",
        "middle_asset",
        "start_asset",
    }

    result = test_up_star.execute_in_process()
    assert result.success
    assert result.output_for_node("middle_asset", "o1") == "foo"
    assert result.output_for_node("follows_o2") == "foo"
    assert result.output_for_node("start_asset") == "foo"

    test_down_star = group.build_job(name="test_down_star", selection="start_asset*")

    assert len(test_down_star.all_node_defs) == 4
    assert set([node.name for node in test_down_star.all_node_defs]) == {
        "follows_o2",
        "middle_asset",
        "start_asset",
        "follows_o1",
    }

    result = test_down_star.execute_in_process()
    assert result.success
    assert result.output_for_node("follows_o2") == "foo"

    test_both_plus = group.build_job(name="test_both_plus", selection=["+o1+", "o2"])

    assert len(test_both_plus.all_node_defs) == 4
    assert set([node.name for node in test_both_plus.all_node_defs]) == {
        "follows_o1",
        "follows_o2",
        "middle_asset",
        "start_asset",
    }

    result = test_both_plus.execute_in_process()
    assert result.success
    assert result.output_for_node("follows_o2") == "foo"

    test_selection_with_overlap = group.build_job(
        name="test_multi_asset_multi_selection", selection=["o1", "o2+"]
    )

    assert len(test_selection_with_overlap.all_node_defs) == 3
    assert set([node.name for node in test_selection_with_overlap.all_node_defs]) == {
        "follows_o1",
        "follows_o2",
        "middle_asset",
    }

    result = test_selection_with_overlap.execute_in_process()
    assert result.success
    assert result.output_for_node("follows_o2") == "foo"

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=r"When attempting to create job 'bad_subset', the clause "
        r"'doesnt_exist' within the asset key selection did not match any asset "
        r"keys. Present asset keys: \['start_asset', 'o1', 'o2', 'follows_o1', 'follows_o2'\]",
    ):
        group.build_job(name="bad_subset", selection="doesnt_exist")

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=r"When attempting to create job 'bad_query_arguments', the clause "
        r"follows_o1= within the asset key selection was invalid. Please review "
        r"the selection syntax here: "
        r"https://docs.dagster.io/concepts/ops-jobs-graphs/job-execution#op-selection-syntax.",
    ):
        group.build_job(name="bad_query_arguments", selection="follows_o1=")

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=r"When building job 'test_subselect_only_one_key', the asset "
        r"'middle_asset' contains asset keys \['o1', 'o2'\], but attempted to "
        r"select only \['o1'\]. Selecting only some of the asset keys for a "
        r"particular asset is not yet supported behavior. Please select all "
        r"asset keys produced by a given asset when subsetting.",
    ):
        group.build_job(name="test_subselect_only_one_key", selection="o1")


def test_asset_group_from_package_name():
    from . import asset_package

    collection = AssetGroup.from_package_name(asset_package.__name__)
    assert len(collection.assets) == 4
    assert {asset.op.name for asset in collection.assets} == {
        "little_richard",
        "miles_davis",
        "chuck_berry",
        "bb_king",
    }
    assert {source_asset.key for source_asset in collection.source_assets} == {
        AssetKey("elvis_presley")
    }


def test_asset_group_from_package_module():
    from . import asset_package

    collection = AssetGroup.from_package_module(asset_package)
    assert len(collection.assets) == 4
    assert {asset.op.name for asset in collection.assets} == {
        "little_richard",
        "miles_davis",
        "chuck_berry",
        "bb_king",
    }
    assert {source_asset.key for source_asset in collection.source_assets} == {
        AssetKey("elvis_presley")
    }


def test_asset_group_from_modules():
    from . import asset_package
    from .asset_package import module_with_assets

    collection = AssetGroup.from_modules([asset_package, module_with_assets])
    assert {asset.op.name for asset in collection.assets} == {
        "little_richard",
        "chuck_berry",
        "miles_davis",
    }
    assert len(collection.assets) == 3
    assert {source_asset.key for source_asset in collection.source_assets} == {
        AssetKey("elvis_presley")
    }


def test_default_io_manager():
    @asset
    def asset_foo():
        return "foo"

    group = AssetGroup(assets=[asset_foo])
    assert (
        group.resource_defs["io_manager"]  # pylint: disable=comparison-with-callable
        == fs_asset_io_manager
    )
