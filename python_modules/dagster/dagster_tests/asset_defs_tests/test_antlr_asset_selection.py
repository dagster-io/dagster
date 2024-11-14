import pytest
from dagster._core.definitions.antlr_asset_selection.antlr_asset_selection import (
    AntlrAssetSelectionParser,
)


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
