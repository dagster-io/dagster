import pytest
from dagster._core.definitions.antlr_asset_selection.antlr_asset_selection import (
    AntlrAssetSelectionParser,
)
from dagster._core.definitions.asset_selection import AssetSelection, CodeLocationAssetSelection
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.storage.tags import KIND_PREFIX


@pytest.mark.parametrize(
    "selection_str, expected_tree_str",
    [
        ("*", "(start (expr *) <EOF>)"),
        (
            "***+++",
            "(start (expr (expr (traversal *) (expr (traversal *) (expr *))) (traversal + + +)) <EOF>)",
        ),
        ("key:a", "(start (expr (attributeExpr key : (value a))) <EOF>)"),
        ("key_substring:a", "(start (expr (attributeExpr key_substring : (value a))) <EOF>)"),
        ('key:"*/a+"', '(start (expr (attributeExpr key : (value "*/a+"))) <EOF>)'),
        (
            'key_substring:"*/a+"',
            '(start (expr (attributeExpr key_substring : (value "*/a+"))) <EOF>)',
        ),
        (
            "sinks(key:a)",
            "(start (expr (functionName sinks) ( (expr (attributeExpr key : (value a))) )) <EOF>)",
        ),
        (
            "roots(key:a)",
            "(start (expr (functionName roots) ( (expr (attributeExpr key : (value a))) )) <EOF>)",
        ),
        ("tag:foo=bar", "(start (expr (attributeExpr tag : (value foo) = (value bar))) <EOF>)"),
        ("owner:billing", "(start (expr (attributeExpr owner : (value billing))) <EOF>)"),
        (
            'group:"my_group"',
            '(start (expr (attributeExpr group : (value "my_group"))) <EOF>)',
        ),
        ("kind:my_kind", "(start (expr (attributeExpr kind : (value my_kind))) <EOF>)"),
        (
            "code_location:my_location",
            "(start (expr (attributeExpr code_location : (value my_location))) <EOF>)",
        ),
        (
            "(((key:a)))",
            "(start (expr ( (expr ( (expr ( (expr (attributeExpr key : (value a))) )) )) )) <EOF>)",
        ),
        (
            "not not key:not",
            "(start (expr not (expr not (expr (attributeExpr key : (value not))))) <EOF>)",
        ),
        (
            "(roots(key:a) and owner:billing)*",
            "(start (expr (expr ( (expr (expr (functionName roots) ( (expr (attributeExpr key : (value a))) )) and (expr (attributeExpr owner : (value billing)))) )) (traversal *)) <EOF>)",
        ),
        (
            "++(key:a+)",
            "(start (expr (traversal + +) (expr ( (expr (expr (attributeExpr key : (value a))) (traversal +)) ))) <EOF>)",
        ),
        (
            "key:a* and *key:b",
            "(start (expr (expr (expr (attributeExpr key : (value a))) (traversal *)) and (expr (traversal *) (expr (attributeExpr key : (value b))))) <EOF>)",
        ),
    ],
)
def test_antlr_tree(selection_str, expected_tree_str):
    asset_selection = AntlrAssetSelectionParser(selection_str)
    assert asset_selection.tree_str == expected_tree_str


@pytest.mark.parametrize(
    "selection_str",
    ["not", "a b", "a and and", "a and", "sinks", "owner", "tag:foo=", "owner:owner@owner.com"],
)
def test_antlr_tree_invalid(selection_str):
    with pytest.raises(Exception):
        AntlrAssetSelectionParser(selection_str)


@pytest.mark.parametrize(
    "selection_str, expected_assets",
    [
        ('"a"', AssetSelection.assets("a")),
        ("not a", AssetSelection.all() - AssetSelection.assets("a")),
        ("a and b", AssetSelection.assets("a") & AssetSelection.assets("b")),
        ("a or b", AssetSelection.assets("a") | AssetSelection.assets("b")),
        ("+a", AssetSelection.assets("a").upstream(1)),
        ("++a", AssetSelection.assets("a").upstream(2)),
        ("a+", AssetSelection.assets("a").downstream(1)),
        ("a++", AssetSelection.assets("a").downstream(2)),
        (
            "a* and *b",
            AssetSelection.assets("a").downstream() and AssetSelection.assets("b").upstream(),
        ),
        ("sinks(a)", AssetSelection.assets("a").sinks()),
        ("roots(c)", AssetSelection.assets("c").roots()),
        ("tag:foo", AssetSelection.tag("foo", "")),
        ("tag:foo=bar", AssetSelection.tag("foo", "bar")),
        ('owner:"owner@owner.com"', AssetSelection.owner("owner@owner.com")),
        ("group:my_group", AssetSelection.groups("my_group")),
        ("kind:my_kind", AssetSelection.tag(f"{KIND_PREFIX}my_kind", "")),
    ],
)
def test_antlr_visit_basic(selection_str, expected_assets):
    # a -> b -> c
    @asset(tags={"foo": "bar"}, owners=["team:billing"])
    def a(): ...

    @asset(deps=[a], kinds={"python", "snowflake"})
    def b(): ...

    @asset(
        deps=[b],
        group_name="my_group",
    )
    def c(): ...

    defs = [a, b, c]

    assert AntlrAssetSelectionParser(selection_str).asset_selection.resolve(
        defs
    ) == expected_assets.resolve(defs)


def test_code_location() -> None:
    @asset
    def my_asset(): ...

    # Selection can be instantiated.
    selection = AntlrAssetSelectionParser("code_location:code_location1").asset_selection

    assert selection == CodeLocationAssetSelection(selected_code_location="code_location1")

    # But not resolved.
    with pytest.raises(NotImplementedError):
        selection.resolve([my_asset])
