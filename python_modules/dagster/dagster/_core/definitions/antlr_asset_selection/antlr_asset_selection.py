from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

from dagster._core.definitions.antlr_asset_selection.generated.AssetSelectionLexer import (
    AssetSelectionLexer,
)
from dagster._core.definitions.antlr_asset_selection.generated.AssetSelectionParser import (
    AssetSelectionParser,
)


class ANTLRInputErrorListener(ErrorListener):
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        raise Exception(f"Syntax error at line {line}, column {column}: {msg}")


class AntlrAssetSelectionParser:
    def __init__(self, selection_str: str):
        lexer = AssetSelectionLexer(InputStream(selection_str))
        lexer.removeErrorListeners()
        lexer.addErrorListener(ANTLRInputErrorListener())

        stream = CommonTokenStream(lexer)

        parser = AssetSelectionParser(stream)
        parser.removeErrorListeners()
        parser.addErrorListener(ANTLRInputErrorListener())

        self._tree = parser.start()
        self._tree_str = self._tree.toStringTree(recog=parser)

    @property
    def tree_str(self) -> str:
        return self._tree_str
