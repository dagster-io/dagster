# Generated from AssetSelection.g4 by ANTLR 4.13.2
from antlr4 import *

if "." in __name__:
    from .AssetSelectionParser import AssetSelectionParser
else:
    from AssetSelectionParser import AssetSelectionParser

# This class defines a complete generic visitor for a parse tree produced by AssetSelectionParser.


class AssetSelectionVisitor(ParseTreeVisitor):
    # Visit a parse tree produced by AssetSelectionParser#start.
    def visitStart(self, ctx: AssetSelectionParser.StartContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#AssetExpression.
    def visitAssetExpression(self, ctx: AssetSelectionParser.AssetExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#ParenthesizedExpression.
    def visitParenthesizedExpression(
        self, ctx: AssetSelectionParser.ParenthesizedExpressionContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#UpTraversalExpression.
    def visitUpTraversalExpression(self, ctx: AssetSelectionParser.UpTraversalExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#AndExpression.
    def visitAndExpression(self, ctx: AssetSelectionParser.AndExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#NotExpression.
    def visitNotExpression(self, ctx: AssetSelectionParser.NotExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#DownTraversalExpression.
    def visitDownTraversalExpression(
        self, ctx: AssetSelectionParser.DownTraversalExpressionContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#OrExpression.
    def visitOrExpression(self, ctx: AssetSelectionParser.OrExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#AttributeExpression.
    def visitAttributeExpression(self, ctx: AssetSelectionParser.AttributeExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#FunctionCallExpression.
    def visitFunctionCallExpression(self, ctx: AssetSelectionParser.FunctionCallExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#UpAndDownTraversalExpression.
    def visitUpAndDownTraversalExpression(
        self, ctx: AssetSelectionParser.UpAndDownTraversalExpressionContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#traversal.
    def visitTraversal(self, ctx: AssetSelectionParser.TraversalContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#functionName.
    def visitFunctionName(self, ctx: AssetSelectionParser.FunctionNameContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#TagAttributeExpr.
    def visitTagAttributeExpr(self, ctx: AssetSelectionParser.TagAttributeExprContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#OwnerAttributeExpr.
    def visitOwnerAttributeExpr(self, ctx: AssetSelectionParser.OwnerAttributeExprContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#GroupAttributeExpr.
    def visitGroupAttributeExpr(self, ctx: AssetSelectionParser.GroupAttributeExprContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#KindAttributeExpr.
    def visitKindAttributeExpr(self, ctx: AssetSelectionParser.KindAttributeExprContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#CodeLocationAttributeExpr.
    def visitCodeLocationAttributeExpr(
        self, ctx: AssetSelectionParser.CodeLocationAttributeExprContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#value.
    def visitValue(self, ctx: AssetSelectionParser.ValueContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#ExactMatchAsset.
    def visitExactMatchAsset(self, ctx: AssetSelectionParser.ExactMatchAssetContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#PrefixMatchAsset.
    def visitPrefixMatchAsset(self, ctx: AssetSelectionParser.PrefixMatchAssetContext):
        return self.visitChildren(ctx)


del AssetSelectionParser
