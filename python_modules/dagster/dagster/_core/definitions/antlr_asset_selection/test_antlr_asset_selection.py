import pytest

from dagster._core.definitions.antlr_asset_selection.antlr_asset_selection import (
    AntlrAssetSelection,
)


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
    asset_selection = AntlrAssetSelection(selection_str)
    assert asset_selection.tree_str == expected_tree_str
