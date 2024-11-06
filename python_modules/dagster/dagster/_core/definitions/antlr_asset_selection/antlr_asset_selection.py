from antlr4 import CommonTokenStream, InputStream

from dagster._annotations import experimental
from dagster._core.definitions.antlr_asset_selection.generated.AssetSelectionLexer import (
    AssetSelectionLexer,
)
from dagster._core.definitions.antlr_asset_selection.generated.AssetSelectionParser import (
    AssetSelectionParser,
)


@experimental
class AntlrAssetSelection:
    def __init__(self, selection_str: str):
        lexer = AssetSelectionLexer(InputStream(selection_str))
        stream = CommonTokenStream(lexer)
        parser = AssetSelectionParser(stream)

        self._tree = parser.start()
        self._tree_str = self._tree.toStringTree(recog=parser)

    @property
    def tree_str(self) -> str:
        return self._tree_str
