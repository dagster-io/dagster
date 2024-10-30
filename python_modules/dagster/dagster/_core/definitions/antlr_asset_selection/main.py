from antlr4 import CommonTokenStream, InputStream

from dagster._core.definitions.antlr_asset_selection.AssetSelectionLexer import AssetSelectionLexer
from dagster._core.definitions.antlr_asset_selection.AssetSelectionParser import (
    AssetSelectionParser,
)
from dagster._core.definitions.antlr_asset_selection.AssetSelectionVisitor import (
    AssetSelectionVisitor,
)

input_text = "hello"
lexer = AssetSelectionLexer(InputStream(input_text))
stream = CommonTokenStream(lexer)
parser = AssetSelectionParser(stream)

tree = parser.expr()

visitor = AssetSelectionVisitor()

# print(tree.toStringTree(recog=parser))
# print(visitor.visit(tree))
