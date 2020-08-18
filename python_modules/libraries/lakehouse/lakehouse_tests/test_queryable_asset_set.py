import pytest
from lakehouse import computed_asset, source_asset
from lakehouse.queryable_asset_set import QueryableAssetSet, generate_dep_graph, path_str


def get_assets():
    """
     // --> b -- \\
    a              d
     \\ --> c -- //

    e --> f
    """
    a = source_asset(path="a")

    @computed_asset(input_assets=[a])
    def b(_):
        pass

    @computed_asset(input_assets=[a])
    def c(_):
        pass

    @computed_asset(input_assets=[b, c])
    def d(_b, _c):
        pass

    e = source_asset(path="e")

    @computed_asset(input_assets=[e])
    def f(_):
        pass

    return a, b, c, d, e, f


def test_generate_dep_graph():
    assets = get_assets()
    dep_graph = generate_dep_graph(assets)
    assert dep_graph == {
        "upstream": {"a": set(), "b": {"a"}, "c": {"a"}, "d": {"b", "c"}, "e": set(), "f": {"e"}},
        "downstream": {"a": {"b", "c"}, "b": {"d"}, "c": {"d"}, "d": set(), "e": {"f"}, "f": set()},
    }


@pytest.mark.parametrize(
    "query, expected_asset_names",
    [
        ("a", {"a"}),
        ("a*", {"a", "b", "c", "d"}),
        ("*b", {"a", "b"}),
        ("*d", {"a", "b", "c", "d"}),
        ("a+", {"a", "b", "c"}),
        ("a++", {"a", "b", "c", "d"}),
        ("+d", {"b", "c", "d"}),
        ("++d", {"a", "b", "c", "d"}),
        ("+a", {"a"}),
        ("d+", {"d"}),
        (None, {"a", "b", "c", "d", "e", "f"}),
    ],
)
def test_parse_solid_selection_single(query, expected_asset_names):
    assets = get_assets()
    queryable_asset_set = QueryableAssetSet(assets)
    result_assets = queryable_asset_set.query_assets(query)
    assert {path_str(asset) for asset in result_assets} == expected_asset_names
