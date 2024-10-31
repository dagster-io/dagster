from antlr4 import CommonTokenStream, InputStream

from dagster._core.definitions.antlr_asset_selection.AssetSelectionLexer import AssetSelectionLexer
from dagster._core.definitions.antlr_asset_selection.AssetSelectionParser import (
    AssetSelectionParser,
)
from dagster._core.definitions.antlr_asset_selection.AssetSelectionVisitor import (
    AssetSelectionVisitor,
)


class AntlrAssetSelection:
    _visitor: AssetSelectionVisitor = AssetSelectionVisitor()

    def __init__(self, selection_str: str):
        lexer = AssetSelectionLexer(InputStream(selection_str))
        stream = CommonTokenStream(lexer)
        parser = AssetSelectionParser(stream)
        self._tree = parser.start()
        self._tree_str = self._tree.toStringTree(recog=parser)

    @property
    def tree_str(self) -> str:
        return self._tree_str

    # def assets(self) -> AssetSelection:
    #     return AntlrAssetSelection._visitor.visit(self._tree)
