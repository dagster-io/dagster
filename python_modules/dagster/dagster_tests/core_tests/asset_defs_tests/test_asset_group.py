import re
import warnings

import pytest

from dagster import (
    AssetKey,
    DagsterEventType,
    DagsterInvalidDefinitionError,
    DailyPartitionsDefinition,
    EventRecordsFilter,
    HourlyPartitionsDefinition,
    IOManager,
    Out,
    Output,
    ResourceDefinition,
    fs_asset_io_manager,
    graph,
    in_process_executor,
    io_manager,
    mem_io_manager,
    multiprocess_executor,
    repository,
    resource,
)
from dagster.core.asset_defs import AssetGroup, AssetIn, SourceAsset, asset, multi_asset
from dagster.core.errors import DagsterInvalidSubsetError, DagsterUnmetExecutorRequirementsError
from dagster.core.test_utils import instance_for_test


def _all_asset_keys(result):
    mats = [
        event.event_specific_data.materialization
        for event in result.all_events
        if event.event_type_value == "ASSET_MATERIALIZATION"
    ]
    ret = {mat.asset_key for mat in mats}
    assert len(mats) == len(ret)
    return ret


@pytest.fixture(autouse=True)
def check_experimental_warnings():
    with warnings.catch_warnings(record=True) as record:
        yield

        raises_warning = False
        for w in record:
            if "build_assets_job" in w.message.args[0] or "root_input_manager" in w.message.args[0]:
                raises_warning = True
                break

        assert not raises_warning


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
    assert AssetGroup.is_base_job_name(asset_group_underlying_job.name)

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
    assert AssetGroup.is_base_job_name(asset_group_underlying_job.name)

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
    assert AssetGroup.is_base_job_name(asset_group_underlying_job.name)

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
        match=r"SourceAsset with key AssetKey\(\['foo'\]\) requires io manager with key 'foo', which was not provided on AssetGroup. Provided keys: \['io_manager'\]",
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
        r"Provided resources: \['io_manager'\]",
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


def _get_assets_defs(use_multi: bool = False, allow_subset: bool = False):
    """
    Dependencies:
        "upstream": {
            "start": set(),
            "a": {"start"},
            "b": set(),
            "c": {"b"},
            "d": {"a", "b"},
            "e": {"c"},
            "f": {"e", "d"},
            "final": {"a", "d"},
        },
        "downstream": {
            "start": {"a"},
            "b": {"c", "d"},
            "a": {"final", "d"},
            "c": {"e"},
            "d": {"final", "f"},
            "e": {"f"},
        }
    """

    @asset
    def start():
        return 1

    @asset
    def a(start):
        return start + 1

    @asset
    def b():
        return 1

    @asset
    def c(b):
        return b + 1

    @multi_asset(
        outs={
            "a": Out(is_required=False),
            "b": Out(is_required=False),
            "c": Out(is_required=False),
        },
        internal_asset_deps={
            "a": {AssetKey("start")},
            "b": set(),
            "c": {AssetKey("b")},
        },
        can_subset=allow_subset,
    )
    def abc_(context, start):
        a = (start + 1) if start else None
        b = 1
        c = b + 1
        out_values = {"a": a, "b": b, "c": c}
        outputs_to_return = context.selected_output_names if allow_subset else "abc"
        for output_name in outputs_to_return:
            yield Output(out_values[output_name], output_name)

    @asset
    def d(a, b):
        return a + b

    @asset
    def e(c):
        return c + 1

    @asset
    def f(d, e):
        return d + e

    @multi_asset(
        outs={
            "d": Out(is_required=False),
            "e": Out(is_required=False),
            "f": Out(is_required=False),
        },
        internal_asset_deps={
            "d": {AssetKey("a"), AssetKey("b")},
            "e": {AssetKey("c")},
            "f": {AssetKey("d"), AssetKey("e")},
        },
        can_subset=allow_subset,
    )
    def def_(context, a, b, c):
        d = (a + b) if a and b else None
        e = (c + 1) if c else None
        f = (d + e) if d and e else None
        out_values = {"d": d, "e": e, "f": f}
        outputs_to_return = context.selected_output_names if allow_subset else "def"
        for output_name in outputs_to_return:
            yield Output(out_values[output_name], output_name)

    @asset
    def final(a, d):
        return a + d

    if use_multi:
        return [start, abc_, def_, final]
    return [start, a, b, c, d, e, f, final]


@pytest.mark.parametrize(
    "job_selection,use_multi,expected_error",
    [
        ("*", False, None),
        ("*", True, None),
        ("e", False, None),
        ("e", True, (DagsterInvalidDefinitionError, "")),
        (
            "x",
            False,
            (
                DagsterInvalidSubsetError,
                r"No qualified assets to execute found for clause='x'",
            ),
        ),
        (
            "x",
            True,
            (
                DagsterInvalidSubsetError,
                r"No qualified assets to execute found for clause='x'",
            ),
        ),
        (
            ["start", "x"],
            False,
            (
                DagsterInvalidSubsetError,
                r"No qualified assets to execute found for clause='x'",
            ),
        ),
        (
            ["start", "x"],
            True,
            (
                DagsterInvalidSubsetError,
                r"No qualified assets to execute found for clause='x'",
            ),
        ),
        (["d", "e", "f"], False, None),
        (["d", "e", "f"], True, None),
        (["*final"], False, None),
        (
            ["*final"],
            True,
            (
                DagsterInvalidDefinitionError,
                r"When building job, the AssetsDefinition 'abc_' contains asset keys "
                r"\[AssetKey\(\['a'\]\), AssetKey\(\['b'\]\), AssetKey\(\['c'\]\)\], but attempted to "
                r"select only \[AssetKey\(\['a'\]\), AssetKey\(\['b'\]\)\]",
            ),
        ),
    ],
)
def test_asset_group_build_subset_job_errors(job_selection, use_multi, expected_error):
    group = AssetGroup(_get_assets_defs(use_multi=use_multi))

    if expected_error:
        expected_class, expected_message = expected_error
        with pytest.raises(expected_class, match=expected_message):
            group.build_job("some_name", selection=job_selection)
    else:
        assert group.build_job("some_name", selection=job_selection)


@pytest.mark.parametrize("use_multi", [True, False])
@pytest.mark.parametrize(
    "job_selection,expected_assets,prefixes",
    [
        ("*", "start,a,b,c,d,e,f,final", None),
        ("a", "a", None),
        ("b+", "b,c,d", None),
        ("+f", "f,d,e", None),
        ("++f", "f,d,e,c,a,b", None),
        ("start*", "start,a,d,f,final", None),
        (["+a", "b+"], "start,a,b,c,d", None),
        (["*c", "final"], "b,c,final", None),
        ("*", "start,a,b,c,d,e,f,final", ["core", "models"]),
        ("core>models>a", "a", ["core", "models"]),
        ("core>models>b+", "b,c,d", ["core", "models"]),
        ("+core>models>f", "f,d,e", ["core", "models"]),
        ("++core>models>f", "f,d,e,c,a,b", ["core", "models"]),
        ("core>models>start*", "start,a,d,f,final", ["core", "models"]),
        (["+core>models>a", "core>models>b+"], "start,a,b,c,d", ["core", "models"]),
        (["*core>models>c", "core>models>final"], "b,c,final", ["core", "models"]),
    ],
)
def test_asset_group_build_subset_job(job_selection, expected_assets, use_multi, prefixes):

    _, io_manager_def = asset_aware_io_manager()
    group = AssetGroup(
        # for these, if we have multi assets, we'll always allow them to be subset
        _get_assets_defs(use_multi=use_multi, allow_subset=use_multi),
        resource_defs={"io_manager": io_manager_def},
    )
    # apply prefixes
    for prefix in reversed(prefixes or []):
        group = group.prefixed(prefix)

    # run once so values exist to load from
    group.build_job("initial").execute_in_process()

    # now build the subset job
    job = group.build_job("assets_job", selection=job_selection)

    with instance_for_test() as instance:
        result = job.execute_in_process(instance=instance)
        planned_asset_keys = {
            record.event_log_entry.dagster_event.event_specific_data.asset_key
            for record in instance.get_event_records(
                EventRecordsFilter(DagsterEventType.ASSET_MATERIALIZATION_PLANNED)
            )
        }

    expected_asset_keys = set(
        (AssetKey([*(prefixes or []), a]) for a in expected_assets.split(","))
    )
    # make sure we've planned on the correct set of keys
    assert planned_asset_keys == expected_asset_keys

    # make sure we've generated the correct set of keys
    assert _all_asset_keys(result) == expected_asset_keys

    if use_multi:
        expected_outputs = {
            "start": 1,
            "abc_.a": 2,
            "abc_.b": 1,
            "abc_.c": 2,
            "def_.d": 3,
            "def_.e": 3,
            "def_.f": 6,
            "final": 5,
        }
    else:
        expected_outputs = {"start": 1, "a": 2, "b": 1, "c": 2, "d": 3, "e": 3, "f": 6, "final": 5}

    # check if the output values are as we expect
    for output, value in expected_outputs.items():
        asset_name = output.split(".")[-1]
        if asset_name in expected_assets.split(","):
            # dealing with multi asset
            if output != asset_name:
                assert result.output_for_node(output.split(".")[0], asset_name)
            # dealing with regular asset
            else:
                assert result.output_for_node(output, "result") == value


def test_subset_does_not_respect_context():
    @asset
    def start():
        return 1

    @multi_asset(outs={"a": Out(), "b": Out(), "c": Out()}, can_subset=True)
    def abc(start):
        # this asset declares that it can subset its computation but will always produce all outputs
        yield Output(1 + start, "a")
        yield Output(2 + start, "b")
        yield Output(3 + start, "c")

    @asset
    def final(c):
        return c + 1

    group = AssetGroup([start, abc, final])
    job = group.build_job("subset_job", selection=["*final"])

    # these are the keys specified by the selection *final
    specified_keys = {AssetKey("start"), AssetKey("c"), AssetKey("final")}

    with instance_for_test() as instance:
        result = job.execute_in_process(instance=instance)
        planned_asset_keys = {
            record.event_log_entry.dagster_event.event_specific_data.asset_key
            for record in instance.get_event_records(
                EventRecordsFilter(DagsterEventType.ASSET_MATERIALIZATION_PLANNED)
            )
        }

    # should only plan on creating keys start, c, final
    assert planned_asset_keys == specified_keys

    # should still emit asset materializations if we generate these outputs
    assert _all_asset_keys(result) == specified_keys | {AssetKey("a"), AssetKey("b")}


def test_asset_group_build_job_selection_multi_component():
    source_asset = SourceAsset(["apple", "banana"])

    @asset(namespace="abc")
    def asset1():
        ...

    group = AssetGroup([asset1], source_assets=[source_asset])
    assert group.build_job(name="something", selection="abc>asset1").asset_layer.asset_keys == {
        AssetKey(["abc", "asset1"])
    }

    with pytest.raises(DagsterInvalidSubsetError, match="No qualified"):
        group.build_job(name="something", selection="apple>banana")


def test_asset_group_from_package_name():
    from . import asset_package

    collection_1 = AssetGroup.from_package_name(asset_package.__name__)
    assert len(collection_1.assets) == 6

    assets_1 = [asset.op.name for asset in collection_1.assets]
    source_assets_1 = [source_asset.key for source_asset in collection_1.source_assets]

    collection_2 = AssetGroup.from_package_name(asset_package.__name__)
    assert len(collection_2.assets) == 6

    assets_2 = [asset.op.name for asset in collection_2.assets]
    source_assets_2 = [source_asset.key for source_asset in collection_2.source_assets]

    assert assets_1 == assets_2
    assert source_assets_1 == source_assets_2


def test_asset_group_from_package_module():
    from . import asset_package

    collection_1 = AssetGroup.from_package_module(asset_package)
    assert len(collection_1.assets) == 6

    assets_1 = [asset.op.name for asset in collection_1.assets]
    source_assets_1 = [source_asset.key for source_asset in collection_1.source_assets]

    collection_2 = AssetGroup.from_package_module(asset_package)
    assert len(collection_2.assets) == 6

    assets_2 = [asset.op.name for asset in collection_2.assets]
    source_assets_2 = [source_asset.key for source_asset in collection_2.source_assets]

    assert assets_1 == assets_2
    assert source_assets_1 == source_assets_2


def test_asset_group_from_modules(monkeypatch):
    from . import asset_package
    from .asset_package import module_with_assets

    collection_1 = AssetGroup.from_modules([asset_package, module_with_assets])

    assets_1 = [asset.op.name for asset in collection_1.assets]
    source_assets_1 = [source_asset.key for source_asset in collection_1.source_assets]

    collection_2 = AssetGroup.from_modules([asset_package, module_with_assets])

    assets_2 = [asset.op.name for asset in collection_2.assets]
    source_assets_2 = [source_asset.key for source_asset in collection_2.source_assets]

    assert assets_1 == assets_2
    assert source_assets_1 == source_assets_2

    with monkeypatch.context() as m:

        @asset
        def little_richard():
            pass

        m.setattr(asset_package, "little_richard_dup", little_richard, raising=False)
        with pytest.raises(
            DagsterInvalidDefinitionError,
            match=re.escape(
                "Asset key AssetKey(['little_richard']) is defined multiple times. "
                "Definitions found in modules: dagster_tests.core_tests.asset_defs_tests.asset_package."
            ),
        ):
            AssetGroup.from_modules([asset_package, module_with_assets])


@asset
def asset_in_current_module():
    pass


source_asset_in_current_module = SourceAsset(AssetKey("source_asset_in_current_module"))


def test_asset_group_from_current_module():
    group = AssetGroup.from_current_module()
    assert {asset.op.name for asset in group.assets} == {"asset_in_current_module"}
    assert len(group.assets) == 1
    assert {source_asset.key for source_asset in group.source_assets} == {
        AssetKey("source_asset_in_current_module")
    }
    assert len(group.source_assets) == 1


def test_default_io_manager():
    @asset
    def asset_foo():
        return "foo"

    group = AssetGroup(assets=[asset_foo])
    assert (
        group.resource_defs["io_manager"]  # pylint: disable=comparison-with-callable
        == fs_asset_io_manager
    )


def test_job_with_reserved_name():
    @graph
    def the_graph():
        pass

    the_job = the_graph.to_job(name="__ASSET_GROUP")
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Attempted to provide job called __ASSET_GROUP to repository, which is a reserved name.",
    ):

        @repository
        def the_repo():  # pylint: disable=unused-variable
            return [the_job]


def test_materialize():
    @asset
    def asset_foo():
        return "foo"

    group = AssetGroup(assets=[asset_foo])

    result = group.materialize()
    assert result.success


def test_materialize_with_out_of_process_executor():
    @asset
    def asset_foo():
        return "foo"

    group = AssetGroup(assets=[asset_foo], executor_def=multiprocess_executor)

    with pytest.raises(
        DagsterUnmetExecutorRequirementsError,
        match="'materialize' can only be invoked on AssetGroups which have no executor or have "
        "the in_process_executor, but the AssetGroup had executor 'multiprocess'",
    ):
        group.materialize()


def test_materialize_with_selection():
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

    result = group.materialize(selection=["*follows_o2", "o1"])
    assert result.success
    assert result.output_for_node("middle_asset", "o1") == "foo"
    assert result.output_for_node("follows_o2") == "foo"
    assert result.output_for_node("start_asset") == "foo"


def test_multiple_partitions_defs():
    @asset(partitions_def=DailyPartitionsDefinition(start_date="2021-05-05"))
    def daily_asset():
        ...

    @asset(partitions_def=DailyPartitionsDefinition(start_date="2021-05-05"))
    def daily_asset2():
        ...

    @asset(partitions_def=DailyPartitionsDefinition(start_date="2020-05-05"))
    def daily_asset_different_start_date():
        ...

    @asset(partitions_def=HourlyPartitionsDefinition(start_date="2021-05-05-00:00"))
    def hourly_asset():
        ...

    @asset
    def unpartitioned_asset():
        ...

    group = AssetGroup(
        [
            daily_asset,
            daily_asset2,
            daily_asset_different_start_date,
            hourly_asset,
            unpartitioned_asset,
        ]
    )

    jobs = group.get_base_jobs()
    assert len(jobs) == 3
    assert {job_def.name for job_def in jobs} == {
        "__ASSET_GROUP_0",
        "__ASSET_GROUP_1",
        "__ASSET_GROUP_2",
    }
    assert {
        frozenset([node_def.name for node_def in job_def.all_node_defs]) for job_def in jobs
    } == {
        frozenset(["daily_asset", "daily_asset2", "unpartitioned_asset"]),
        frozenset(["hourly_asset", "unpartitioned_asset"]),
        frozenset(["daily_asset_different_start_date", "unpartitioned_asset"]),
    }


def test_assets_prefixed_single_asset():
    @asset
    def asset1():
        ...

    result = AssetGroup([asset1]).prefixed("my_prefix").assets
    assert result[0].asset_key == AssetKey(["my_prefix", "asset1"])


def test_assets_prefixed_internal_dep():
    @asset
    def asset1():
        ...

    @asset
    def asset2(asset1):
        del asset1

    result = AssetGroup([asset1, asset2]).prefixed("my_prefix").assets
    assert result[0].asset_key == AssetKey(["my_prefix", "asset1"])
    assert result[1].asset_key == AssetKey(["my_prefix", "asset2"])
    assert set(result[1].dependency_asset_keys) == {AssetKey(["my_prefix", "asset1"])}


def test_assets_prefixed_disambiguate():
    asset1 = SourceAsset(AssetKey(["core", "apple"]))

    @asset(name="apple")
    def asset2():
        ...

    @asset(ins={"apple": AssetIn(namespace="core")})
    def orange(apple):
        del apple

    @asset
    def banana(apple):
        del apple

    result = (
        AssetGroup([asset2, orange, banana], source_assets=[asset1]).prefixed("my_prefix").assets
    )
    assert len(result) == 3
    assert result[0].asset_key == AssetKey(["my_prefix", "apple"])
    assert result[1].asset_key == AssetKey(["my_prefix", "orange"])
    assert set(result[1].dependency_asset_keys) == {AssetKey(["core", "apple"])}
    assert result[2].asset_key == AssetKey(["my_prefix", "banana"])
    assert set(result[2].dependency_asset_keys) == {AssetKey(["my_prefix", "apple"])}


def test_assets_prefixed_source_asset():
    asset1 = SourceAsset(key=AssetKey(["upstream_prefix", "asset1"]))

    @asset(ins={"asset1": AssetIn(namespace="upstream_prefix")})
    def asset2(asset1):
        del asset1

    result = AssetGroup([asset2], source_assets=[asset1]).prefixed("my_prefix").assets
    assert len(result) == 1
    assert result[0].asset_key == AssetKey(["my_prefix", "asset2"])
    assert set(result[0].dependency_asset_keys) == {AssetKey(["upstream_prefix", "asset1"])}


def test_assets_prefixed_no_matches():
    @asset
    def orange(apple):
        del apple

    result = AssetGroup([orange]).prefixed("my_prefix").assets
    assert result[0].asset_key == AssetKey(["my_prefix", "orange"])
    assert set(result[0].dependency_asset_keys) == {AssetKey("apple")}


def test_add_asset_groups():
    @asset
    def asset1():
        ...

    @asset
    def asset2():
        ...

    source1 = SourceAsset(AssetKey(["source1"]))
    source2 = SourceAsset(AssetKey(["source2"]))

    group1 = AssetGroup(assets=[asset1], source_assets=[source1])
    group2 = AssetGroup(assets=[asset2], source_assets=[source2])

    assert (group1 + group2) == AssetGroup(
        assets=[asset1, asset2], source_assets=[source1, source2]
    )


def test_add_asset_groups_different_resources():
    @asset
    def asset1():
        ...

    @asset
    def asset2():
        ...

    source1 = SourceAsset(AssetKey(["source1"]))
    source2 = SourceAsset(AssetKey(["source2"]))

    group1 = AssetGroup(
        assets=[asset1],
        source_assets=[source1],
        resource_defs={"apple": ResourceDefinition.none_resource()},
    )
    group2 = AssetGroup(
        assets=[asset2],
        source_assets=[source2],
        resource_defs={"banana": ResourceDefinition.none_resource()},
    )

    with pytest.raises(DagsterInvalidDefinitionError):
        group1 + group2  # pylint: disable=pointless-statement


def test_add_asset_groups_different_executors():
    @asset
    def asset1():
        ...

    @asset
    def asset2():
        ...

    source1 = SourceAsset(AssetKey(["source1"]))
    source2 = SourceAsset(AssetKey(["source2"]))

    group1 = AssetGroup(assets=[asset1], source_assets=[source1], executor_def=in_process_executor)
    group2 = AssetGroup(
        assets=[asset2],
        source_assets=[source2],
    )

    with pytest.raises(DagsterInvalidDefinitionError):
        group1 + group2  # pylint: disable=pointless-statement


def test_to_source_assets():
    @asset
    def my_asset():
        ...

    @multi_asset(
        outs={
            "my_out_name": Out(asset_key=AssetKey("my_asset_name")),
            "my_other_out_name": Out(asset_key=AssetKey("my_other_asset")),
        }
    )
    def my_multi_asset():
        yield Output(1, "my_out_name")
        yield Output(2, "my_other_out_name")

    assert AssetGroup([my_asset, my_multi_asset]).to_source_assets() == [
        SourceAsset(AssetKey(["my_asset"])),
        SourceAsset(AssetKey(["my_asset_name"])),
        SourceAsset(AssetKey(["my_other_asset"])),
    ]
