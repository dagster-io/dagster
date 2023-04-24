import hashlib
import warnings

import pytest
from dagster import (
    AssetKey,
    AssetOut,
    AssetsDefinition,
    DagsterEventType,
    EventRecordsFilter,
    IOManager,
    Out,
    Output,
    graph,
    io_manager,
    op,
)
from dagster._core.definitions import AssetGroup, SourceAsset, asset, multi_asset
from dagster._core.definitions.assets_job import build_assets_job
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
    """Get a predefined set of assets definitions for testing.

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
                node_def_name = output.split(".")[0]
                keys_for_node = {AssetKey([*(prefixes or []), c]) for c in node_def_name[:-1]}
                selected_keys_for_node = keys_for_node.intersection(expected_asset_keys)
                if selected_keys_for_node != keys_for_node:
                    node_def_name += (
                        "_subset_"
                        + hashlib.md5(
                            (str(list(sorted(selected_keys_for_node)))).encode()
                        ).hexdigest()[-5:]
                    )
                assert result.output_for_node(node_def_name, asset_name)
            # dealing with regular asset
            else:
                assert result.output_for_node(output, "result") == value


def test_subset_cycle_resolution_embed_assets_in_complex_graph():
    """This represents a single large multi-asset with two assets embedded inside of it.

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
    assert result.output_for_node("foo_subset_53118", "h") == 12


def test_subset_cycle_resolution_complex():
    """Test cycle resolution.

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
    assert result.output_for_node("foo_subset_e9ef2", "f") == 9


def test_subset_cycle_resolution_basic():
    """Ops:
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
    assert result.output_for_node("foo_subset_8e776", "a") == 1
    assert result.output_for_node("foo_prime_subset_b3f31", "a_prime") == 2
    assert result.output_for_node("foo_subset_aa707", "b") == 3
    assert result.output_for_node("foo_prime_subset_52d36", "b_prime") == 4

    assert _all_asset_keys(result) == {
        AssetKey("a"),
        AssetKey("b"),
        AssetKey("a_prime"),
        AssetKey("b_prime"),
    }
