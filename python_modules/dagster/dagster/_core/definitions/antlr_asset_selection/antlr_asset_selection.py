from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

from dagster._core.definitions.antlr_asset_selection.generated.AssetSelectionLexer import (
    AssetSelectionLexer,
)
from dagster._core.definitions.antlr_asset_selection.generated.AssetSelectionParser import (
    AssetSelectionParser,
)
from dagster._core.definitions.antlr_asset_selection.generated.AssetSelectionVisitor import (
    AssetSelectionVisitor,
)
from dagster._core.definitions.asset_selection import AssetSelection


class AntlrInputErrorListener(ErrorListener):
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        raise Exception(f"Syntax error at line {line}, column {column}: {msg}")


class AntlrAssetSelectionParser:
    _visitor: AssetSelectionVisitor = AssetSelectionVisitor()

    def __init__(self, selection_str: str):
        lexer = AssetSelectionLexer(InputStream(selection_str))
        lexer.removeErrorListeners()
        lexer.addErrorListener(AntlrInputErrorListener())

        stream = CommonTokenStream(lexer)

        parser = AssetSelectionParser(stream)
        parser.removeErrorListeners()
        parser.addErrorListener(AntlrInputErrorListener())

        self._tree = parser.start()
        self._tree_str = self._tree.toStringTree(recog=parser)
        self._asset_selection = self._visitor.visit(self._tree)

    @property
    def tree_str(self) -> str:
        return self._tree_str

    @property
    def asset_selection(self) -> AssetSelection:
        return self._asset_selection
