from typing import List

import pytest

from dagster import (
    AssetKey,
    AssetSelection,
    AssetsDefinition,
    DagsterEventType,
    EventRecordsFilter,
    IOManager,
    Out,
    Output,
    define_asset_job,
    graph,
    in_process_executor,
    io_manager,
    op,
)
from dagster.core.asset_defs import asset, multi_asset
from dagster.core.errors import DagsterInvalidSubsetError
from dagster.core.execution.with_resources import with_resources
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


def _apply_prefix(assets_defs, key_prefix):
    asset_keys = {asset_key for assets_def in assets_defs for asset_key in assets_def.asset_keys}

    result_assets: List[AssetsDefinition] = []
    for assets_def in assets_defs:
        output_asset_key_replacements = {
            asset_key: AssetKey([key_prefix] + asset_key.path)
            for asset_key in assets_def.asset_keys
        }
        input_asset_key_replacements = {}
        for dep_asset_key in assets_def.dependency_asset_keys:
            if dep_asset_key in asset_keys:
                input_asset_key_replacements[dep_asset_key] = AssetKey(
                    (key_prefix, *dep_asset_key.path)
                )

        result_assets.append(
            assets_def.with_replaced_asset_keys(
                output_asset_key_replacements=output_asset_key_replacements,
                input_asset_key_replacements=input_asset_key_replacements,
            )
        )
    return result_assets


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
        ("e", True, (DagsterInvalidSubsetError, "")),
        (
            "x",
            False,
            (DagsterInvalidSubsetError, r"When building job, the AssetKey\(s\) \['x'\]"),
        ),
        (
            "x",
            True,
            (DagsterInvalidSubsetError, r"When building job, the AssetKey\(s\) \['x'\]"),
        ),
        (
            ["start", "x"],
            False,
            (DagsterInvalidSubsetError, r"When building job, the AssetKey\(s\) \['x'\]"),
        ),
        (
            ["start", "x"],
            True,
            (DagsterInvalidSubsetError, r"When building job, the AssetKey\(s\) \['x'\]"),
        ),
        (["d", "e", "f"], False, None),
        (["d", "e", "f"], True, None),
        (["*final"], False, None),
        (
            ["*final"],
            True,
            (
                DagsterInvalidSubsetError,
                r"When building job, the AssetsDefinition 'abc_' contains asset keys "
                r"\[AssetKey\(\['a'\]\), AssetKey\(\['b'\]\), AssetKey\(\['c'\]\)\], but attempted to "
                r"select only \[AssetKey\(\['a'\]\), AssetKey\(\['b'\]\)\]",
            ),
        ),
    ],
)
def test_resolve_subset_job_errors(job_selection, use_multi, expected_error):
    job_def = define_asset_job(name="some_name", selection=job_selection)
    if expected_error:
        expected_class, expected_message = expected_error
        with pytest.raises(expected_class, match=expected_message):
            job_def.resolve(assets=_get_assets_defs(use_multi), source_assets=[])
    else:
        assert job_def.resolve(assets=_get_assets_defs(use_multi), source_assets=[])


@pytest.mark.parametrize(
    "job_selection,expected_assets",
    [
        (None, "a,b,c"),
        ("a+", "a,b"),
        ("+c", "b,c"),
        (["a", "c"], "a,c"),
        (AssetSelection.keys("a", "c") | AssetSelection.keys("c", "b"), "a,b,c"),
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
    final_assets = with_resources([a_asset, b_asset, c_asset], {"asset_io_manager": io_manager_def})

    # run once so values exist to load from
    define_asset_job("initial").resolve(final_assets, source_assets=[]).execute_in_process()

    # now build the subset job
    job = define_asset_job("asset_job", selection=job_selection).resolve(
        final_assets, source_assets=[]
    )

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
        (AssetSelection.all(), "start,a,b,c,d,e,f,final", None),
        (AssetSelection.keys("a", "b", "c"), "a,b,c", None),
        (AssetSelection.keys("f").upstream(depth=1), "f,d,e", None),
        (AssetSelection.keys("f").upstream(depth=2), "f,d,e,c,a,b", None),
        (AssetSelection.keys("start").downstream(), "start,a,d,f,final", None),
        (
            AssetSelection.keys("a").upstream(depth=1)
            | AssetSelection.keys("b").downstream(depth=1),
            "start,a,b,c,d",
            None,
        ),
        (AssetSelection.keys("c").upstream() | AssetSelection.keys("final"), "b,c,final", None),
        (AssetSelection.all(), "start,a,b,c,d,e,f,final", ["core", "models"]),
        (
            AssetSelection.keys("core/models/a").upstream(depth=1)
            | AssetSelection.keys("core/models/b").downstream(depth=1),
            "start,a,b,c,d",
            ["core", "models"],
        ),
    ],
)
def test_define_selection_job(job_selection, expected_assets, use_multi, prefixes):

    _, io_manager_def = asset_aware_io_manager()
    # for these, if we have multi assets, we'll always allow them to be subset
    prefixed_assets = _get_assets_defs(use_multi=use_multi, allow_subset=use_multi)
    # apply prefixes
    for prefix in reversed(prefixes or []):
        prefixed_assets = _apply_prefix(prefixed_assets, prefix)

    final_assets = with_resources(
        prefixed_assets,
        resource_defs={"io_manager": io_manager_def},
    )

    # run once so values exist to load from
    define_asset_job("initial").resolve(final_assets, source_assets=[]).execute_in_process()

    # now build the subset job
    job = define_asset_job("asset_job", selection=job_selection).resolve(
        final_assets, source_assets=[]
    )

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


@asset
def foo():
    return 1


@pytest.mark.skip()
def test_executor_def():
    job = define_asset_job("with_exec", executor_def=in_process_executor).resolve([foo], [])
    assert job.executor_def == in_process_executor  # pylint: disable=comparison-with-callable


def test_tags():
    my_tags = {"foo": "bar"}
    job = define_asset_job("with_tags", tags=my_tags).resolve([foo], [])
    assert job.tags == my_tags


def test_description():
    description = "Some very important description"
    job = define_asset_job("with_tags", description=description).resolve([foo], [])
    assert job.description == description
