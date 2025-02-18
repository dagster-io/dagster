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
from dagster._core.definitions.asset_selection import (
    AssetSelection,
    ChangedInBranchAssetSelection,
    CodeLocationAssetSelection,
    ColumnAssetSelection,
    ColumnTagAssetSelection,
    KeyWildCardAssetSelection,
    TableNameAssetSelection,
)
from dagster._core.storage.tags import KIND_PREFIX


class AntlrInputErrorListener(ErrorListener):
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        raise Exception(f"Syntax error at line {line}, column {column}: {msg}")


def parse_traversal_depth(optional_digits):
    """Return an integer from DIGITS text if present, otherwise None (meaning infinite depth)."""
    if optional_digits is None:
        return None
    return int(optional_digits.getText())


class AntlrAssetSelectionVisitor(AssetSelectionVisitor):
    def __init__(self, include_sources: bool):
        self.include_sources = include_sources

    def visitStart(self, ctx: AssetSelectionParser.StartContext):
        return self.visit(ctx.expr())

    def visitTraversalAllowedExpression(
        self, ctx: AssetSelectionParser.TraversalAllowedExpressionContext
    ):
        return self.visit(ctx.traversalAllowedExpr())

    def visitUpAndDownTraversalExpression(
        self, ctx: AssetSelectionParser.UpAndDownTraversalExpressionContext
    ):
        selection: AssetSelection = self.visit(ctx.traversalAllowedExpr())
        # upTraversal => optional DIGITS? PLUS
        up_digits = ctx.upTraversal().DIGITS()
        up_depth = parse_traversal_depth(up_digits)

        # downTraversal => PLUS DIGITS?
        down_digits = ctx.downTraversal().DIGITS()
        down_depth = parse_traversal_depth(down_digits)

        return selection.upstream(depth=up_depth) | selection.downstream(depth=down_depth)

    def visitUpTraversalExpression(self, ctx: AssetSelectionParser.UpTraversalExpressionContext):
        selection: AssetSelection = self.visit(ctx.traversalAllowedExpr())
        up_digits = ctx.upTraversal().DIGITS()
        up_depth = parse_traversal_depth(up_digits)
        return selection.upstream(depth=up_depth)

    def visitDownTraversalExpression(
        self, ctx: AssetSelectionParser.DownTraversalExpressionContext
    ):
        selection: AssetSelection = self.visit(ctx.traversalAllowedExpr())
        down_digits = ctx.downTraversal().DIGITS()
        down_depth = parse_traversal_depth(down_digits)
        return selection.downstream(depth=down_depth)

    def visitNotExpression(self, ctx: AssetSelectionParser.NotExpressionContext):
        selection: AssetSelection = self.visit(ctx.expr())
        return AssetSelection.all(include_sources=self.include_sources) - selection

    def visitAndExpression(self, ctx: AssetSelectionParser.AndExpressionContext):
        left: AssetSelection = self.visit(ctx.expr(0))
        right: AssetSelection = self.visit(ctx.expr(1))
        return left & right

    def visitOrExpression(self, ctx: AssetSelectionParser.OrExpressionContext):
        left: AssetSelection = self.visit(ctx.expr(0))
        right: AssetSelection = self.visit(ctx.expr(1))
        return left | right

    def visitAllExpression(self, ctx: AssetSelectionParser.AllExpressionContext):
        return AssetSelection.all(include_sources=self.include_sources)

    def visitAttributeExpression(self, ctx: AssetSelectionParser.AttributeExpressionContext):
        return self.visit(ctx.attributeExpr())

    def visitFunctionCallExpression(self, ctx: AssetSelectionParser.FunctionCallExpressionContext):
        function = self.visit(ctx.functionName())
        selection: AssetSelection = self.visit(ctx.expr())
        if function == "sinks":
            return selection.sinks()
        elif function == "roots":
            return selection.roots()

    def visitParenthesizedExpression(
        self, ctx: AssetSelectionParser.ParenthesizedExpressionContext
    ):
        return self.visit(ctx.expr())

    def visitFunctionName(self, ctx: AssetSelectionParser.FunctionNameContext):
        if ctx.SINKS():
            return "sinks"
        elif ctx.ROOTS():
            return "roots"

    def visitKeyExpr(self, ctx: AssetSelectionParser.KeyExprContext):
        value = self.visit(ctx.keyValue())
        return KeyWildCardAssetSelection(selected_key_wildcard=value)

    def visitTagAttributeExpr(self, ctx: AssetSelectionParser.TagAttributeExprContext):
        key = self.visit(ctx.value(0))
        value = self.visit(ctx.value(1)) if ctx.EQUAL() else ""
        return AssetSelection.tag(key, value, include_sources=self.include_sources)

    def visitOwnerAttributeExpr(self, ctx: AssetSelectionParser.OwnerAttributeExprContext):
        owner = self.visit(ctx.value())
        return AssetSelection.owner(owner)

    def visitGroupAttributeExpr(self, ctx: AssetSelectionParser.GroupAttributeExprContext):
        group = self.visit(ctx.value())
        return AssetSelection.groups(group, include_sources=self.include_sources)

    def visitKindAttributeExpr(self, ctx: AssetSelectionParser.KindAttributeExprContext):
        kind = self.visit(ctx.value())
        return AssetSelection.tag(f"{KIND_PREFIX}{kind}", "", include_sources=self.include_sources)

    def visitCodeLocationAttributeExpr(
        self, ctx: AssetSelectionParser.CodeLocationAttributeExprContext
    ):
        code_location = self.visit(ctx.value())
        return CodeLocationAssetSelection(selected_code_location=code_location)

    def visitKeyValue(self, ctx: AssetSelectionParser.KeyValueContext):
        if ctx.QUOTED_STRING():
            return ctx.QUOTED_STRING().getText().strip('"')
        elif ctx.UNQUOTED_WILDCARD_STRING():
            return ctx.UNQUOTED_WILDCARD_STRING().getText()
        elif ctx.UNQUOTED_STRING():
            return ctx.UNQUOTED_STRING().getText()

    def visitValue(self, ctx: AssetSelectionParser.ValueContext):
        if ctx.QUOTED_STRING():
            return ctx.QUOTED_STRING().getText().strip('"')
        elif ctx.UNQUOTED_STRING():
            return ctx.UNQUOTED_STRING().getText()

    def visitColumnAttributeExpr(self, ctx: AssetSelectionParser.ColumnAttributeExprContext):
        column = self.visit(ctx.value())
        return ColumnAssetSelection(selected_column=column)

    def visitTableNameAttributeExpr(self, ctx: AssetSelectionParser.TableNameAttributeExprContext):
        table_name = self.visit(ctx.value())
        return TableNameAssetSelection(selected_table_name=table_name)

    def visitColumnTagAttributeExpr(self, ctx: AssetSelectionParser.ColumnTagAttributeExprContext):
        key = self.visit(ctx.value(0))
        value = self.visit(ctx.value(1)) if ctx.EQUAL() else ""
        return ColumnTagAssetSelection(key=key, value=value)

    def visitChangedInBranchAttributeExpr(
        self, ctx: AssetSelectionParser.ChangedInBranchAttributeExprContext
    ):
        branch = self.visit(ctx.value())
        return ChangedInBranchAssetSelection(selected_changed_in_branch=branch)


class AntlrAssetSelectionParser:
    def __init__(self, selection_str: str, include_sources: bool = False):
        lexer = AssetSelectionLexer(InputStream(selection_str))
        lexer.removeErrorListeners()  # Remove the default listener that just writes to the console
        lexer.addErrorListener(AntlrInputErrorListener())

        stream = CommonTokenStream(lexer)

        parser = AssetSelectionParser(stream)
        parser.removeErrorListeners()  # Remove the default listener that just writes to the console
        parser.addErrorListener(AntlrInputErrorListener())

        self._tree = parser.start()
        self._tree_str = self._tree.toStringTree(recog=parser)
        self._asset_selection = AntlrAssetSelectionVisitor(include_sources).visit(self._tree)

    @property
    def tree_str(self) -> str:
        return self._tree_str

    @property
    def asset_selection(self) -> AssetSelection:
        return self._asset_selection
