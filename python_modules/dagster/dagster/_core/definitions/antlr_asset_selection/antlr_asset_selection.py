from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

from dagster._annotations import experimental
from dagster._core.definitions.antlr_asset_selection.generated.AssetSelectionLexer import (
    AssetSelectionLexer,
)
from dagster._core.definitions.antlr_asset_selection.generated.AssetSelectionParser import (
    AssetSelectionParser,
)
from dagster._core.definitions.antlr_asset_selection.generated.AssetSelectionVisitor import (
    AssetSelectionVisitor,
)
from dagster._core.definitions.asset_selection import AssetSelection, CodeLocationAssetSelection
from dagster._core.storage.tags import KIND_PREFIX


class AntlrInputErrorListener(ErrorListener):
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        raise Exception(f"Syntax error at line {line}, column {column}: {msg}")


class AntlrAssetSelectionVisitor(AssetSelectionVisitor):
    # Visit a parse tree produced by AssetSelectionParser#start.
    def visitStart(self, ctx: AssetSelectionParser.StartContext):
        return self.visit(ctx.expr())

    # Visit a parse tree produced by AssetSelectionParser#AssetExpression.
    def visitAssetExpression(self, ctx: AssetSelectionParser.AssetExpressionContext):
        return self.visit(ctx.assetExpr())

    # Visit a parse tree produced by AssetSelectionParser#ParenthesizedExpression.
    def visitParenthesizedExpression(
        self, ctx: AssetSelectionParser.ParenthesizedExpressionContext
    ):
        return self.visit(ctx.expr())

    # Visit a parse tree produced by AssetSelectionParser#UpTraversalExpression.
    def visitUpTraversalExpression(self, ctx: AssetSelectionParser.UpTraversalExpressionContext):
        selection: AssetSelection = self.visit(ctx.expr())
        traversal_depth = self.visit(ctx.traversal())
        return selection.upstream(depth=traversal_depth)

    # Visit a parse tree produced by AssetSelectionParser#AndExpression.
    def visitAndExpression(self, ctx: AssetSelectionParser.AndExpressionContext):
        left: AssetSelection = self.visit(ctx.expr(0))
        right: AssetSelection = self.visit(ctx.expr(1))
        return left & right

    # Visit a parse tree produced by AssetSelectionParser#NotExpression.
    def visitNotExpression(self, ctx: AssetSelectionParser.NotExpressionContext):
        selection: AssetSelection = self.visit(ctx.expr())
        return AssetSelection.all() - selection

    # Visit a parse tree produced by AssetSelectionParser#DownTraversalExpression.
    def visitDownTraversalExpression(
        self, ctx: AssetSelectionParser.DownTraversalExpressionContext
    ):
        selection: AssetSelection = self.visit(ctx.expr())
        traversal_depth = self.visit(ctx.traversal())
        return selection.downstream(depth=traversal_depth)

    # Visit a parse tree produced by AssetSelectionParser#OrExpression.
    def visitOrExpression(self, ctx: AssetSelectionParser.OrExpressionContext):
        left: AssetSelection = self.visit(ctx.expr(0))
        right: AssetSelection = self.visit(ctx.expr(1))
        return left | right

    # Visit a parse tree produced by AssetSelectionParser#AttributeExpression.
    def visitAttributeExpression(self, ctx: AssetSelectionParser.AttributeExpressionContext):
        return self.visit(ctx.attributeExpr())

    # Visit a parse tree produced by AssetSelectionParser#FunctionCallExpression.
    def visitFunctionCallExpression(self, ctx: AssetSelectionParser.FunctionCallExpressionContext):
        function = self.visit(ctx.functionName())
        selection: AssetSelection = self.visit(ctx.expr())
        if function == "sinks":
            return selection.sinks()
        elif function == "roots":
            return selection.roots()

    # Visit a parse tree produced by AssetSelectionParser#UpAndDownTraversalExpression.
    def visitUpAndDownTraversalExpression(
        self, ctx: AssetSelectionParser.UpAndDownTraversalExpressionContext
    ):
        selection: AssetSelection = self.visit(ctx.expr())
        up_depth = self.visit(ctx.traversal(0))
        down_depth = self.visit(ctx.traversal(1))
        return selection.upstream(depth=up_depth) | selection.downstream(depth=down_depth)

    # Visit a parse tree produced by AssetSelectionParser#traversal.
    def visitTraversal(self, ctx: AssetSelectionParser.TraversalContext):
        # Get traversal depth from a traversal context
        if ctx.STAR():
            return None  # Star means no depth limit
        elif ctx.PLUS():
            return len(ctx.PLUS())  # Depth is the count of '+'

    # Visit a parse tree produced by AssetSelectionParser#functionName.
    def visitFunctionName(self, ctx: AssetSelectionParser.FunctionNameContext):
        if ctx.SINKS():
            return "sinks"
        elif ctx.ROOTS():
            return "roots"

    # Visit a parse tree produced by AssetSelectionParser#TagAttributeExpr.
    def visitTagAttributeExpr(self, ctx: AssetSelectionParser.TagAttributeExprContext):
        key = self.visit(ctx.value(0))
        value = self.visit(ctx.value(1)) if ctx.EQUAL() else ""
        return AssetSelection.tag(key, value)

    # Visit a parse tree produced by AssetSelectionParser#OwnerAttributeExpr.
    def visitOwnerAttributeExpr(self, ctx: AssetSelectionParser.OwnerAttributeExprContext):
        owner = self.visit(ctx.value())
        return AssetSelection.owner(owner)

    # Visit a parse tree produced by AssetSelectionParser#GroupAttributeExpr.
    def visitGroupAttributeExpr(self, ctx: AssetSelectionParser.GroupAttributeExprContext):
        group = self.visit(ctx.value())
        return AssetSelection.groups(group)

    # Visit a parse tree produced by AssetSelectionParser#KindAttributeExpr.
    def visitKindAttributeExpr(self, ctx: AssetSelectionParser.KindAttributeExprContext):
        kind = self.visit(ctx.value())
        return AssetSelection.tag(f"{KIND_PREFIX}{kind}", "")

    # Visit a parse tree produced by AssetSelectionParser#CodeLocationAttributeExpr.
    def visitCodeLocationAttributeExpr(
        self, ctx: AssetSelectionParser.CodeLocationAttributeExprContext
    ):
        code_location = self.visit(ctx.value())
        return CodeLocationAssetSelection(selected_code_location=code_location)

    # Visit a parse tree produced by AssetSelectionParser#value.
    def visitValue(self, ctx: AssetSelectionParser.ValueContext):
        if ctx.QUOTED_STRING():
            return ctx.QUOTED_STRING().getText().strip('"')
        elif ctx.UNQUOTED_STRING():
            return ctx.UNQUOTED_STRING().getText()

    # Visit a parse tree produced by AssetSelectionParser#ExactMatchAsset.
    def visitExactMatchAsset(self, ctx: AssetSelectionParser.ExactMatchAssetContext):
        asset = ctx.QUOTED_STRING().getText().strip('"')
        return AssetSelection.assets(asset)

    # Visit a parse tree produced by AssetSelectionParser#PrefixMatchAsset.
    def visitPrefixMatchAsset(self, ctx: AssetSelectionParser.PrefixMatchAssetContext):
        asset = ctx.UNQUOTED_STRING().getText()
        return AssetSelection.key_prefixes(asset)


@experimental
class AntlrAssetSelectionParser:
    _visitor: AntlrAssetSelectionVisitor = AntlrAssetSelectionVisitor()

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
