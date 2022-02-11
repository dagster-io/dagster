import pytest
from dagster import (
    AssetKey,
    DagsterInvalidDefinitionError,
    IOManager,
    Out,
    in_process_executor,
    io_manager,
    mem_io_manager,
    repository,
    resource,
)
from dagster.core.asset_defs import AssetCollection, AssetIn, SourceAsset, asset, multi_asset


def test_asset_collection_from_list():
    @asset
    def asset_foo():
        return "foo"

    @asset
    def asset_bar():
        return "bar"

    @asset(ins={"asset_bar": AssetIn(asset_key=AssetKey("asset_foo"))})
    def last_asset(asset_bar):
        return asset_bar

    collection = AssetCollection(assets=[asset_foo, asset_bar, last_asset])

    @repository
    def the_repo():
        return [collection]

    assert len(the_repo.get_all_jobs()) == 1
    asset_collection_underlying_job = the_repo.get_all_jobs()[0]
    assert asset_collection_underlying_job.name == collection.all_assets_job_name

    result = asset_collection_underlying_job.execute_in_process()
    assert result.success


def test_asset_collection_source_asset():
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

    collection = AssetCollection(
        assets=[asset_depends_on_source],
        source_assets=[foo_fa],
        resource_defs={"the_manager": the_manager},
    )

    @repository
    def the_repo():
        return [collection]

    asset_collection_underlying_job = the_repo.get_all_jobs()[0]
    assert asset_collection_underlying_job.name == collection.all_assets_job_name

    result = asset_collection_underlying_job.execute_in_process()
    assert result.success


def test_asset_collection_with_resources():
    @asset(required_resource_keys={"foo"})
    def asset_foo(context):
        return context.resources.foo

    @resource
    def the_resource():
        return "foo"

    collection = AssetCollection([asset_foo], resource_defs={"foo": the_resource})

    @repository
    def the_repo():
        return [collection]

    asset_collection_underlying_job = the_repo.get_all_jobs()[0]
    assert asset_collection_underlying_job.name == collection.all_assets_job_name

    result = asset_collection_underlying_job.execute_in_process()
    assert result.success
    assert result.output_for_node("asset_foo") == "foo"


def test_asset_collection_missing_resources():
    @asset(required_resource_keys={"foo"})
    def asset_foo(context):
        return context.resources.foo

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=r"AssetCollection is missing required resource keys for asset 'asset_foo'. Missing resource keys: \['foo'\]",
    ):
        AssetCollection([asset_foo])

    source_asset_io_req = SourceAsset(key=AssetKey("foo"), io_manager_key="foo")

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=r"SourceAsset with key AssetKey\(\['foo'\]\) requires io manager with key 'foo', which was not provided on AssetCollection. Provided keys: \['io_manager', 'root_manager'\]",
    ):
        AssetCollection([], source_assets=[source_asset_io_req])


def test_asset_collection_with_executor():
    @asset
    def the_asset():
        pass

    @repository
    def the_repo():
        return [AssetCollection([the_asset], executor_def=in_process_executor)]

    asset_collection_underlying_job = the_repo.get_all_jobs()[0]
    assert (
        asset_collection_underlying_job.executor_def  # pylint: disable=comparison-with-callable
        == in_process_executor
    )


def test_asset_collection_requires_root_manager():
    @asset(io_manager_key="blah")
    def asset_foo():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=r"Output 'result' with AssetKey 'AssetKey\(\['asset_foo'\]\)' requires io manager 'blah' but was not provided on asset collection. Provided resources: \['io_manager', 'root_manager'\]",
    ):
        AssetCollection([asset_foo])


def test_resource_override():
    @resource
    def the_resource():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Resource dictionary included resource with key 'root_manager', which is a reserved resource keyword in Dagster. Please change this key, and then change all places that require this key to a new value.",
    ):
        AssetCollection([], resource_defs={"root_manager": the_resource})

    @repository
    def the_repo():
        return [AssetCollection([], resource_defs={"io_manager": mem_io_manager})]

    asset_collection_underlying_job = the_repo.get_all_jobs()[0]
    assert (  # pylint: disable=comparison-with-callable
        asset_collection_underlying_job.resource_defs["io_manager"] == mem_io_manager
    )


def test_asset_collection_build_subset_job():
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

    collection = AssetCollection([start_asset, middle_asset, follows_o1, follows_o2])

    full_job = collection.build_job("full", asset_key_selection="*")
    result = full_job.execute_in_process()
    assert result.success
    assert result.output_for_node("follows_o1") == "foo"
    assert result.output_for_node("follows_o2") == "foo"

    test_single = collection.build_job(name="test_single", asset_key_selection="follows_o2")
    assert len(test_single.all_node_defs) == 1
    assert test_single.all_node_defs[0].name == "follows_o2"

    test_up_star = collection.build_job(name="test_up_star", asset_key_selection="*follows_o2")
    assert len(test_up_star.all_node_defs) == 3
    assert set([node.name for node in test_up_star.all_node_defs]) == {
        "follows_o2",
        "middle_asset",
        "start_asset",
    }

    test_down_star = collection.build_job(name="test_down_star", asset_key_selection="start_asset*")
    assert len(test_down_star.all_node_defs) == 4
    assert set([node.name for node in test_down_star.all_node_defs]) == {
        "follows_o2",
        "middle_asset",
        "start_asset",
        "follows_o1",
    }

    test_both_plus = collection.build_job(name="test_both_plus", asset_key_selection="+o1+")
    assert len(test_both_plus.all_node_defs) == 4
    assert set([node.name for node in test_both_plus.all_node_defs]) == {
        "follows_o1",
        "follows_o2",
        "middle_asset",
        "start_asset",
    }

    test_selection_with_overlap = collection.build_job(
        name="test_multi_asset_multi_selection", asset_key_selection=["o1", "o2+"]
    )
    assert len(test_selection_with_overlap.all_node_defs) == 3
    assert set([node.name for node in test_selection_with_overlap.all_node_defs]) == {
        "follows_o1",
        "follows_o2",
        "middle_asset",
    }

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=r"When attempting to create job 'bad_subset', the clause 'doesnt_exist' within the asset key selection did not match any asset keys. Present asset keys: \['start_asset', 'o1', 'o2', 'follows_o1', 'follows_o2'\]",
    ):
        collection.build_job(name="bad_subset", asset_key_selection="doesnt_exist")

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=r"When attempting to create job 'bad_query_arguments', the clause follows_o1= within the asset key selection was invalid. Please review the selection syntax here \(imagine there is a link here to the docs\).",
    ):
        collection.build_job(name="bad_query_arguments", asset_key_selection="follows_o1=")
