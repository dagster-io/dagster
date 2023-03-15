import re
import warnings

import pytest
from dagster import (
    AssetKey,
    AssetOut,
    AssetsDefinition,
    DagsterEventType,
    DagsterInvalidDefinitionError,
    EventRecordsFilter,
    IOManager,
    Out,
    Output,
    ResourceDefinition,
    graph,
    in_process_executor,
    io_manager,
    multiprocess_executor,
    op,
    repository,
)
from dagster._core.definitions import AssetGroup, AssetIn, SourceAsset, asset, multi_asset
from dagster._core.definitions.assets_job import build_assets_job
from dagster._core.errors import DagsterInvalidSubsetError, DagsterUnmetExecutorRequirementsError
from dagster._core.test_utils import instance_for_test


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
        # turn off any outer warnings filters
        warnings.resetwarnings()

        yield

        raises_warning = False
        for w in record:
            if "build_assets_job" in w.message.args[0] or "root_input_manager" in w.message.args[0]:
                raises_warning = True
                break

        assert not raises_warning


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
    Get a predefined set of assets definitions for testing.

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
            "a": AssetOut(is_required=False),
            "b": AssetOut(is_required=False),
            "c": AssetOut(is_required=False),
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
            "d": AssetOut(is_required=False),
            "e": AssetOut(is_required=False),
            "f": AssetOut(is_required=False),
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
        ("e", True, (DagsterInvalidSubsetError, "")),
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
        (["start+"], False, None),
        (
            ["start+"],
            True,
            (
                DagsterInvalidSubsetError,
                r"When building job, the AssetsDefinition 'abc_' contains asset keys "
                r"\[AssetKey\(\['a'\]\), AssetKey\(\['b'\]\), AssetKey\(\['c'\]\)\], but"
                r" attempted to "
                r"select only \[AssetKey\(\['a'\]\)\]",
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


@pytest.mark.parametrize(
    "job_selection,expected_assets",
    [
        ("*", "a,b,c"),
        ("a+", "a,b"),
        ("+c", "b,c"),
        (["a", "c"], "a,c"),
    ],
)
def test_simple_graph_backed_asset_subset(job_selection, expected_assets):
    @op
    def one():
        return 1

    @op
    def add_one(x):
        return x + 1

    @op(out=Out(io_manager_key="asset_io_manager"))
    def create_asset(x):
        return x * 2

    @graph
    def a():
        return create_asset(add_one(add_one(one())))

    @graph
    def b(a):
        return create_asset(add_one(add_one(a)))

    @graph
    def c(b):
        return create_asset(add_one(add_one(b)))

    a_asset = AssetsDefinition.from_graph(a)
    b_asset = AssetsDefinition.from_graph(b)
    c_asset = AssetsDefinition.from_graph(c)

    _, io_manager_def = asset_aware_io_manager()
    group = AssetGroup(
        [a_asset, b_asset, c_asset],
        resource_defs={"asset_io_manager": io_manager_def},
    )

    # run once so values exist to load from
    group.build_job("initial").execute_in_process()

    # now build the subset job
    job = group.build_job("assets_job", selection=job_selection)

    result = job.execute_in_process()

    expected_asset_keys = set((AssetKey(a) for a in expected_assets.split(",")))

    # make sure we've generated the correct set of keys
    assert _all_asset_keys(result) == expected_asset_keys

    if AssetKey("a") in expected_asset_keys:
        # (1 + 1 + 1) * 2
        assert result.output_for_node("a.create_asset") == 6
    if AssetKey("b") in expected_asset_keys:
        # (6 + 1 + 1) * 8
        assert result.output_for_node("b.create_asset") == 16
    if AssetKey("c") in expected_asset_keys:
        # (16 + 1 + 1) * 2
        assert result.output_for_node("c.create_asset") == 36


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
        ("core/models/a", "a", ["core", "models"]),
        ("core/models/b+", "b,c,d", ["core", "models"]),
        ("+core/models/f", "f,d,e", ["core", "models"]),
        ("++core/models/f", "f,d,e,c,a,b", ["core", "models"]),
        ("core/models/start*", "start,a,d,f,final", ["core", "models"]),
        (["+core/models/a", "core/models/b+"], "start,a,b,c,d", ["core", "models"]),
        (["*core/models/c", "core/models/final"], "b,c,final", ["core", "models"]),
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

    @multi_asset(outs={"a": AssetOut(), "b": AssetOut(), "c": AssetOut()}, can_subset=True)
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


def test_subset_cycle_resolution_embed_assets_in_complex_graph():
    """
    This represents a single large multi-asset with two assets embedded inside of it.

    Ops:
        foo produces: a, b, c, d, e, f, g, h
        x produces: x
        y produces: y

    Upstream Assets:
        a: []
        b: []
        c: [b]
        d: [b]
        e: [x, c]
        f: [d]
        g: [e]
        h: [g, y]
        x: [a]
        y: [e, f].
    """
    io_manager_obj, io_manager_def = asset_aware_io_manager()
    for item in "abcdefghxy":
        io_manager_obj.db[AssetKey(item)] = None

    @multi_asset(
        outs={name: AssetOut(is_required=False) for name in "a,b,c,d,e,f,g,h".split(",")},
        internal_asset_deps={
            "a": set(),
            "b": set(),
            "c": {AssetKey("b")},
            "d": {AssetKey("b")},
            "e": {AssetKey("c"), AssetKey("x")},
            "f": {AssetKey("d")},
            "g": {AssetKey("e")},
            "h": {AssetKey("g"), AssetKey("y")},
        },
        can_subset=True,
    )
    def foo(context, x, y):
        a = b = c = d = e = f = g = h = None
        if "a" in context.selected_output_names:
            a = 1
            yield Output(a, "a")
        if "b" in context.selected_output_names:
            b = 1
            yield Output(b, "b")
        if "c" in context.selected_output_names:
            c = (b or 1) + 1
            yield Output(c, "c")
        if "d" in context.selected_output_names:
            d = (b or 1) + 1
            yield Output(d, "d")
        if "e" in context.selected_output_names:
            e = x + (c or 2)
            yield Output(e, "e")
        if "f" in context.selected_output_names:
            f = (d or 1) + 1
            yield Output(f, "f")
        if "g" in context.selected_output_names:
            g = (e or 4) + 1
            yield Output(g, "g")
        if "h" in context.selected_output_names:
            h = (g or 5) + y
            yield Output(h, "h")

    @asset
    def x(a):
        return a + 1

    @asset
    def y(e, f):
        return e + f

    job = build_assets_job("a", [foo, x, y], resource_defs={"io_manager": io_manager_def})

    # should produce a job with foo(a,b,c,d,f) -> x -> foo(e,g) -> y -> foo(h)
    assert len(list(job.graph.iterate_op_defs())) == 5
    result = job.execute_in_process()

    assert _all_asset_keys(result) == {AssetKey(x) for x in "a,b,c,d,e,f,g,h,x,y".split(",")}
    assert result.output_for_node("foo_3", "h") == 12


def test_subset_cycle_resolution_complex():
    """
    Test cycle resolution.

    Ops:
        foo produces: a, b, c, d, e, f
        x produces: x
        y produces: y
        z produces: z

    Upstream Assets:
        a: []
        b: [x]
        c: [x]
        d: [y]
        e: [c]
        f: [d]
        x: [a]
        y: [b, c].
    """
    io_manager_obj, io_manager_def = asset_aware_io_manager()
    for item in "abcdefxy":
        io_manager_obj.db[AssetKey(item)] = None

    @multi_asset(
        outs={name: AssetOut(is_required=False) for name in "a,b,c,d,e,f".split(",")},
        internal_asset_deps={
            "a": set(),
            "b": {AssetKey("x")},
            "c": {AssetKey("x")},
            "d": {AssetKey("y")},
            "e": {AssetKey("c")},
            "f": {AssetKey("d")},
        },
        can_subset=True,
    )
    def foo(context, x, y):
        if "a" in context.selected_output_names:
            yield Output(1, "a")
        if "b" in context.selected_output_names:
            yield Output(x + 1, "b")
        if "c" in context.selected_output_names:
            c = x + 2
            yield Output(c, "c")
        if "d" in context.selected_output_names:
            d = y + 1
            yield Output(d, "d")
        if "e" in context.selected_output_names:
            yield Output(c + 1, "e")
        if "f" in context.selected_output_names:
            yield Output(d + 1, "f")

    @asset
    def x(a):
        return a + 1

    @asset
    def y(b, c):
        return b + c

    job = build_assets_job("a", [foo, x, y], resource_defs={"io_manager": io_manager_def})

    # should produce a job with foo -> x -> foo -> y -> foo
    assert len(list(job.graph.iterate_op_defs())) == 5
    result = job.execute_in_process()

    assert _all_asset_keys(result) == {AssetKey(x) for x in "a,b,c,d,e,f,x,y".split(",")}
    assert result.output_for_node("x") == 2
    assert result.output_for_node("y") == 7
    assert result.output_for_node("foo_3", "f") == 9


def test_subset_cycle_resolution_basic():
    """
    Ops:
        foo produces: a, b
        foo_prime produces: a', b'
    Assets:
        s -> a -> a' -> b -> b'.
    """
    io_manager_obj, io_manager_def = asset_aware_io_manager()
    for item in "a,b,a_prime,b_prime".split(","):
        io_manager_obj.db[AssetKey(item)] = None
    # some value for the source
    io_manager_obj.db[AssetKey("s")] = 0

    s = SourceAsset("s")

    @multi_asset(
        outs={"a": AssetOut(is_required=False), "b": AssetOut(is_required=False)},
        internal_asset_deps={
            "a": {AssetKey("s")},
            "b": {AssetKey("a_prime")},
        },
        can_subset=True,
    )
    def foo(context, s, a_prime):
        context.log.info(context.selected_asset_keys)
        if AssetKey("a") in context.selected_asset_keys:
            yield Output(s + 1, "a")
        if AssetKey("b") in context.selected_asset_keys:
            yield Output(a_prime + 1, "b")

    @multi_asset(
        outs={"a_prime": AssetOut(is_required=False), "b_prime": AssetOut(is_required=False)},
        internal_asset_deps={
            "a_prime": {AssetKey("a")},
            "b_prime": {AssetKey("b")},
        },
        can_subset=True,
    )
    def foo_prime(context, a, b):
        context.log.info(context.selected_asset_keys)
        if AssetKey("a_prime") in context.selected_asset_keys:
            yield Output(a + 1, "a_prime")
        if AssetKey("b_prime") in context.selected_asset_keys:
            yield Output(b + 1, "b_prime")

    job = build_assets_job(
        "a", [foo, foo_prime], source_assets=[s], resource_defs={"io_manager": io_manager_def}
    )

    # should produce a job with foo -> foo_prime -> foo_2 -> foo_prime_2
    assert len(list(job.graph.iterate_op_defs())) == 4

    result = job.execute_in_process()
    assert result.output_for_node("foo", "a") == 1
    assert result.output_for_node("foo_prime", "a_prime") == 2
    assert result.output_for_node("foo_2", "b") == 3
    assert result.output_for_node("foo_prime_2", "b_prime") == 4

    assert _all_asset_keys(result) == {
        AssetKey("a"),
        AssetKey("b"),
        AssetKey("a_prime"),
        AssetKey("b_prime"),
    }


def test_cycle_resolution_impossible():
    from toposort import CircularDependencyError

    @asset
    def a(s, c):
        return s + c

    @asset
    def b(a):
        return a + 1

    @asset
    def c(b):
        return b + 1

    s = SourceAsset(key="s")
    with pytest.raises(CircularDependencyError):
        build_assets_job("job", [a, b, c], source_assets=[s])


def test_asset_group_build_job_selection_multi_component():
    source_asset = SourceAsset(["apple", "banana"])

    @asset(key_prefix="abc")
    def asset1():
        ...

    group = AssetGroup([asset1], source_assets=[source_asset])
    assert group.build_job(name="something", selection="abc/asset1").asset_layer.asset_keys == {
        AssetKey(["abc", "asset1"])
    }

    with pytest.raises(DagsterInvalidSubsetError, match="No qualified"):
        group.build_job(name="something", selection="apple/banana")


@pytest.mark.parametrize(
    "job_selection,expected_nodes", [("*", "n1,n2,n3"), ("n2+", "n2,n3"), ("n1", "n1")]
)
def test_asset_group_io_managers(job_selection, expected_nodes):
    # we're testing that when this job is subset, the correct io managers are used to load each
    # source asset
    @io_manager(config_schema={"n": int})
    def return_n_io_manager(context):
        class ReturnNIOManager(IOManager):
            def handle_output(self, _context, obj):
                pass

            def load_input(self, _context):
                return context.resource_config["n"]

        return ReturnNIOManager()

    _ACTUAL_OUTPUT_VAL = 99999

    @asset(io_manager_key="n1_iom")
    def n1():
        return _ACTUAL_OUTPUT_VAL

    @asset(io_manager_key="n2_iom")
    def n2(n1):
        assert n1 == 1
        return _ACTUAL_OUTPUT_VAL

    @asset(io_manager_key="n3_iom")
    def n3(n1, n2):
        assert n1 == 1
        assert n2 == 2
        return _ACTUAL_OUTPUT_VAL

    result = (
        AssetGroup(
            [n1, n2, n3],
            resource_defs={
                "n1_iom": return_n_io_manager.configured({"n": 1}),
                "n2_iom": return_n_io_manager.configured({"n": 2}),
                "n3_iom": return_n_io_manager.configured({"n": 3}),
            },
        )
        .build_job("test", selection=job_selection)
        .execute_in_process()
    )

    for node in expected_nodes.split(","):
        assert result.output_for_node(node) == _ACTUAL_OUTPUT_VAL


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
                "Definitions found in modules: dagster_tests.asset_defs_tests.asset_package."
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


def test_job_with_reserved_name():
    @graph
    def the_graph():
        pass

    the_job = the_graph.to_job(name="__ASSET_JOB")
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "Attempted to provide job called __ASSET_JOB to repository, which is a reserved name."
        ),
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


def test_materialize_with_config():
    @asset(config_schema={"foo": str})
    def asset_foo(context):
        return context.op_config["foo"]

    group = AssetGroup(assets=[asset_foo])

    result = group.materialize(run_config={"ops": {"asset_foo": {"config": {"foo": "bar"}}}})
    assert result.success


def test_materialize_with_out_of_process_executor():
    @asset
    def asset_foo():
        return "foo"

    group = AssetGroup(assets=[asset_foo], executor_def=multiprocess_executor)

    with pytest.raises(
        DagsterUnmetExecutorRequirementsError,
        match=(
            "'materialize' can only be invoked on AssetGroups which have no executor or have "
            "the in_process_executor, but the AssetGroup had executor 'multiprocess'"
        ),
    ):
        group.materialize()


def test_materialize_with_selection():
    @asset
    def start_asset():
        return "foo"

    @multi_asset(outs={"o1": AssetOut(), "o2": AssetOut()})
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


def test_assets_prefixed_single_asset():
    @asset
    def asset1():
        ...

    result = AssetGroup([asset1]).prefixed("my_prefix").assets
    assert result[0].key == AssetKey(["my_prefix", "asset1"])


def test_assets_prefixed_internal_dep():
    @asset
    def asset1():
        ...

    @asset
    def asset2(asset1):
        del asset1

    result = AssetGroup([asset1, asset2]).prefixed("my_prefix").assets
    assert result[0].key == AssetKey(["my_prefix", "asset1"])
    assert result[1].key == AssetKey(["my_prefix", "asset2"])
    assert set(result[1].dependency_keys) == {AssetKey(["my_prefix", "asset1"])}


def test_assets_prefixed_disambiguate():
    asset1 = SourceAsset(AssetKey(["core", "apple"]))

    @asset(name="apple")
    def asset2():
        ...

    @asset(ins={"apple": AssetIn(key_prefix="core")})
    def orange(apple):
        del apple

    @asset
    def banana(apple):
        del apple

    result = (
        AssetGroup([asset2, orange, banana], source_assets=[asset1]).prefixed("my_prefix").assets
    )
    assert len(result) == 3
    assert result[0].key == AssetKey(["my_prefix", "apple"])
    assert result[1].key == AssetKey(["my_prefix", "orange"])
    assert set(result[1].dependency_keys) == {AssetKey(["core", "apple"])}
    assert result[2].key == AssetKey(["my_prefix", "banana"])
    assert set(result[2].dependency_keys) == {AssetKey(["my_prefix", "apple"])}


def test_assets_prefixed_source_asset():
    asset1 = SourceAsset(key=AssetKey(["upstream_prefix", "asset1"]))

    @asset(ins={"asset1": AssetIn(key_prefix="upstream_prefix")})
    def asset2(asset1):
        del asset1

    result = AssetGroup([asset2], source_assets=[asset1]).prefixed("my_prefix").assets
    assert len(result) == 1
    assert result[0].key == AssetKey(["my_prefix", "asset2"])
    assert set(result[0].dependency_keys) == {AssetKey(["upstream_prefix", "asset1"])}


def test_assets_prefixed_no_matches():
    @asset
    def orange(apple):
        del apple

    result = AssetGroup([orange]).prefixed("my_prefix").assets
    assert result[0].key == AssetKey(["my_prefix", "orange"])
    assert set(result[0].dependency_keys) == {AssetKey("apple")}


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

    added_group = group1 + group2
    assert len(added_group.assets) == 2
    assert sorted([asset.key.to_string() for asset in added_group.assets]) == [
        AssetKey(["asset1"]).to_string(),
        AssetKey(["asset2"]).to_string(),
    ]

    assert sorted([asset.key.to_string() for asset in added_group.source_assets]) == [
        AssetKey(["source1"]).to_string(),
        AssetKey(["source2"]).to_string(),
    ]


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
        group1 + group2


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
        group1 + group2
