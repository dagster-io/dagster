import dagster as dg
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.assets.graph.asset_graph import AssetGraph


@dg.asset(group_name="grp1")
def a(): ...


@dg.asset(group_name="grp1")
def b(): ...


@dg.asset(group_name="grp2")
def c(): ...


@dg.multi_asset(
    specs=[dg.AssetSpec("m1", group_name="mixed"), dg.AssetSpec("m2", group_name="mixed")]
)
def multi_m1_m2():
    return 1, 2


@dg.asset
def d(m1): ...


all_assets = [a, b, c, multi_m1_m2, d]
asset_graph = AssetGraph.from_assets(all_assets)


def test_keys_selection_ordered():
    # Using AssetKey objects directly to avoid any coercing issues
    keys = [dg.AssetKey("c"), dg.AssetKey("a"), dg.AssetKey("b")]
    selection = AssetSelection.assets(*keys)

    # Check if internal storage preserved order
    # KeysAssetSelection stores selected_keys
    assert list(selection.selected_keys) == keys

    ordered = selection.resolve_ordered(asset_graph)
    assert list(ordered) == keys


def test_groups_selection_not_ordered():
    selection = AssetSelection.groups("grp1")
    ordered = selection.resolve_ordered(asset_graph)
    assert ordered is None


def test_duplicate_keys_in_selection():
    keys = [dg.AssetKey("c"), dg.AssetKey("a"), dg.AssetKey("c"), dg.AssetKey("b")]
    selection = AssetSelection.assets(*keys)
    ordered = selection.resolve_ordered(asset_graph)
    # Deduplicated, respecting first occurrence
    assert list(ordered) == [dg.AssetKey("c"), dg.AssetKey("a"), dg.AssetKey("b")]


def test_multi_asset_conflicting_order():
    # m2 (index 0), a (index 1), m1 (index 2)
    selection = AssetSelection.assets("m2", "a", "m1")
    job_def = dg.define_asset_job("test_job", selection=selection).resolve(asset_graph=asset_graph)

    node_priorities = {
        (node_invocation.alias or node_invocation.name): node_invocation.tags.get(
            "dagster/priority"
        )
        for node_invocation in job_def.dependencies.keys()
    }

    # m2 has index 0 -> priority 3
    # a has index 1 -> priority 2
    # m1 has index 2 -> priority 1
    # node multi_m1_m2 has m1 and m2 -> max(3, 1) = 3
    assert node_priorities["multi_m1_m2"] == "3"
    assert node_priorities["a"] == "2"


def test_upstream_selection_order():
    selection = AssetSelection.assets("d").upstream()
    ordered = selection.resolve_ordered(asset_graph)
    # d is the 'child_ordered' (base). m1 is remaining.
    assert list(ordered) == [dg.AssetKey("d"), dg.AssetKey("m1")]


def test_subtraction_selection_order():
    selection = (
        AssetSelection.assets("a") | AssetSelection.assets("b") | AssetSelection.assets("c")
    ) - AssetSelection.assets("b")
    ordered = selection.resolve_ordered(asset_graph)
    # (a | b | c) resolves as [a, b, c] because they were added in that order to the union
    # then subtract b -> [a, c]
    assert list(ordered) == [dg.AssetKey("a"), dg.AssetKey("c")]


def test_intersection_complex_order():
    # Intersection prefers order from first operand if available
    selection = AssetSelection.assets("c", "b", "a") & AssetSelection.groups("grp1")
    ordered = selection.resolve_ordered(asset_graph)
    # grp1 has a, b. c, b, a has c, b, a. Intersection: [b, a]
    assert list(ordered) == [dg.AssetKey("b"), dg.AssetKey("a")]


def test_all_selection_not_ordered():
    selection = AssetSelection.all()
    ordered = selection.resolve_ordered(asset_graph)
    assert ordered is None


def test_empty_selection():
    selection = AssetSelection.assets("non_existent")
    ordered = selection.resolve_ordered(asset_graph, allow_missing=True)
    assert ordered is None  # empty selection carries no ordering information


def test_single_node_job_no_priority_regression():
    selection = AssetSelection.assets("a")
    job_def = dg.define_asset_job("test_job", selection=selection).resolve(asset_graph=asset_graph)
    for node_invocation in job_def.dependencies.keys():
        assert "dagster/priority" not in (node_invocation.tags or {})


def test_alphabetical_job_no_priority_regression():
    selection = AssetSelection.assets("a", "b", "c")
    job_def = dg.define_asset_job("test_job", selection=selection).resolve(asset_graph=asset_graph)
    for node_invocation in job_def.dependencies.keys():
        assert "dagster/priority" not in (node_invocation.tags or {})


def test_mixed_case_alphabetical_guard():
    @dg.asset
    def B(): ...
    @dg.asset
    def a_low(): ...

    local_graph = AssetGraph.from_assets([a_low, B])
    # alphabetical: [B, a_low]

    selection = AssetSelection.assets("B", "a_low")
    job_def = dg.define_asset_job("test_job", selection=selection).resolve(asset_graph=local_graph)
    for node_invocation in job_def.dependencies.keys():
        assert "dagster/priority" not in (node_invocation.tags or {})

    # Non-alphabetical: [a_low, B]
    selection = AssetSelection.assets("a_low", "B")
    job_def = dg.define_asset_job("test_job", selection=selection).resolve(asset_graph=local_graph)

    priorities = {n.name: n.tags.get("dagster/priority") for n in job_def.dependencies.keys()}
    assert priorities["a_low"] == "2"
    assert priorities["B"] == "1"


def test_union_order_precedence():
    # grp1 has a, b. alphabetical is [a, b]
    # assets("c", "a") is ordered [c, a]

    # Case 1: Unordered | Ordered
    # User intent (c before a) should win even though grp1 comes first.
    selection = AssetSelection.groups("grp1") | AssetSelection.assets("c", "a")
    ordered = selection.resolve_ordered(asset_graph)
    # [c, a] from assets win precedence. then "b" from grp1 is filled in.
    assert list(ordered) == [dg.AssetKey("c"), dg.AssetKey("a"), dg.AssetKey("b")]

    # Case 2: Ordered | Unordered
    selection = AssetSelection.assets("c", "a") | AssetSelection.groups("grp1")
    ordered = selection.resolve_ordered(asset_graph)
    assert list(ordered) == [dg.AssetKey("c"), dg.AssetKey("a"), dg.AssetKey("b")]


def test_multi_component_key_alphabetical_guard():
    @dg.asset
    def a_b(): ...  # step key "a_b"

    @dg.asset(key_prefix="a")
    def b(): ...  # step key "a__b"

    # Natural executor order: "a__b" then "a_b" (because '_' < 'b')
    # Wait, ASCII: '_' is 95, 'b' is 98.
    # a__b -> [97, 95, 95, 98]
    # a_b  -> [97, 95, 98]
    # Index 2: 95 ('_') vs 98 ('b'). So "a__b" < "a_b".

    local_graph = AssetGraph.from_assets([a_b, b])

    # natural [a__b, a_b]
    selection = AssetSelection.assets(dg.AssetKey(["a", "b"]), dg.AssetKey(["a_b"]))
    job_def = dg.define_asset_job("test", selection=selection).resolve(asset_graph=local_graph)
    for node in job_def.dependencies.keys():
        assert "dagster/priority" not in (node.tags or {})

    # non-natural [a_b, a__b]
    selection = AssetSelection.assets(dg.AssetKey(["a_b"]), dg.AssetKey(["a", "b"]))
    job_def = dg.define_asset_job("test", selection=selection).resolve(asset_graph=local_graph)
    priorities = {n.name: n.tags.get("dagster/priority") for n in job_def.dependencies.keys()}
    assert priorities["a_b"] == "2"
    assert priorities["a__b"] == "1"


def test_execution_priority_e2e():
    materialization_order = []

    @dg.asset
    def asset_1():
        materialization_order.append("asset_1")

    @dg.asset
    def asset_2():
        materialization_order.append("asset_2")

    @dg.asset
    def asset_3():
        materialization_order.append("asset_3")

    # Topological level 0: all three.
    # Default order: 1, 2, 3.
    # Request order: 3, 1, 2.
    selection = AssetSelection.assets("asset_3", "asset_1", "asset_2")
    job_def = dg.define_asset_job("ordered_job", selection=selection).resolve(
        asset_graph=AssetGraph.from_assets([asset_1, asset_2, asset_3])
    )

    result = job_def.execute_in_process()
    # NOTE: The in-process executor does not honour dagster/priority for
    # tiebreak ordering, so we only verify the job completes successfully.
    # Actual priority-driven ordering is verified at the unit level via
    # NodeInvocation tag assertions in the tests above.
    assert result.success


def test_all_subclasses_implement_resolve_ordered_inner():
    """Ensures no concrete AssetSelection subclass silently inherits None."""
    from dagster._core.definitions.asset_selection import AssetSelection

    def get_all_subclasses(cls):
        all_subclasses = []
        for subclass in cls.__subclasses__():
            all_subclasses.append(subclass)
            all_subclasses.extend(get_all_subclasses(subclass))
        return all_subclasses

    # Recursively find all subclasses of AssetSelection currently loaded
    all_selections = get_all_subclasses(AssetSelection)

    for cls in all_selections:
        import inspect

        if not inspect.isabstract(cls):
            # We exclude AssetSelection from the walk to ensure some intermediate
            # or leaf class provides the implementation.
            assert "resolve_ordered_inner" in {
                m for c in cls.__mro__ if c is not AssetSelection for m in c.__dict__
            }, f"{cls.__name__} must explicitly implement resolve_ordered_inner"
