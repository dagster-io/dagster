import pytest

from dagster._core.definitions.antlr_asset_selection.antlr_asset_selection import (
    AntlrAssetSelectionParser,
)
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.storage.tags import KIND_PREFIX


@pytest.mark.parametrize(
    "selection_str, expected_tree_str",
    [
        ('"a"', '(start (expr (assetExpr "a")) <EOF>)'),
        ('sinks("a")', '(start (expr (functionName sinks) ( (expr (assetExpr "a")) )) <EOF>)'),
        ('roots("a")', '(start (expr (functionName roots) ( (expr (assetExpr "a")) )) <EOF>)'),
        ("tag:foo=bar", "(start (expr (attributeExpr tag : (value foo) = (value bar))) <EOF>)"),
        ("owner:billing", "(start (expr (attributeExpr owner : (value billing))) <EOF>)"),
        (
            'group:"my_group"',
            '(start (expr (attributeExpr group : (value "my_group"))) <EOF>)',
        ),
        ("kind:my_kind", "(start (expr (attributeExpr kind : (value my_kind))) <EOF>)"),
        (
            "codelocation:my_location",
            "(start (expr (attributeExpr codelocation : (value my_location))) <EOF>)",
        ),
        (
            '((("a")))',
            '(start (expr ( (expr ( (expr ( (expr (assetExpr "a")) )) )) )) <EOF>)',
        ),
        ('not not "not"', '(start (expr not (expr not (expr (assetExpr "not")))) <EOF>)'),
        (
            '(roots("a") and owner:billing)*',
            '(start (expr (expr ( (expr (expr (functionName roots) ( (expr (assetExpr "a")) )) and (expr (attributeExpr owner : (value billing)))) )) (traversal *)) <EOF>)',
        ),
        (
            '++("a"+)',
            '(start (expr (traversal + +) (expr ( (expr (expr (assetExpr "a")) (traversal +)) ))) <EOF>)',
        ),
        (
            '"a"* and *"b"',
            '(start (expr (expr (expr (assetExpr "a")) (traversal *)) and (expr (traversal *) (expr (assetExpr "b")))) <EOF>)',
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

    assets = AntlrAssetSelectionParser(selection_str).assets()
    assert assets == expected_assets.assets()
