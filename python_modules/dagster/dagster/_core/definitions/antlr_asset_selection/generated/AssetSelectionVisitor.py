# flake8: noqa
# type: ignore
# Generated from AssetSelection.g4 by ANTLR 4.13.2
from antlr4 import *
from .AssetSelectionParser import AssetSelectionParser
# This class defines a complete generic visitor for a parse tree produced by AssetSelectionParser.


class AssetSelectionVisitor(ParseTreeVisitor):
    # Visit a parse tree produced by AssetSelectionParser#start.
    def visitStart(self, ctx: AssetSelectionParser.StartContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#UpTraversalExpression.
    def visitUpTraversalExpression(self, ctx: AssetSelectionParser.UpTraversalExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#AndExpression.
    def visitAndExpression(self, ctx: AssetSelectionParser.AndExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#AllExpression.
    def visitAllExpression(self, ctx: AssetSelectionParser.AllExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#TraversalAllowedExpression.
    def visitTraversalAllowedExpression(
        self, ctx: AssetSelectionParser.TraversalAllowedExpressionContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#DownTraversalExpression.
    def visitDownTraversalExpression(
        self, ctx: AssetSelectionParser.DownTraversalExpressionContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#NotExpression.
    def visitNotExpression(self, ctx: AssetSelectionParser.NotExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#OrExpression.
    def visitOrExpression(self, ctx: AssetSelectionParser.OrExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#UpAndDownTraversalExpression.
    def visitUpAndDownTraversalExpression(
        self, ctx: AssetSelectionParser.UpAndDownTraversalExpressionContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#AttributeExpression.
    def visitAttributeExpression(self, ctx: AssetSelectionParser.AttributeExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#FunctionCallExpression.
    def visitFunctionCallExpression(self, ctx: AssetSelectionParser.FunctionCallExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#ParenthesizedExpression.
    def visitParenthesizedExpression(
        self, ctx: AssetSelectionParser.ParenthesizedExpressionContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#upTraversal.
    def visitUpTraversal(self, ctx: AssetSelectionParser.UpTraversalContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#downTraversal.
    def visitDownTraversal(self, ctx: AssetSelectionParser.DownTraversalContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#functionName.
    def visitFunctionName(self, ctx: AssetSelectionParser.FunctionNameContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#KeyExpr.
    def visitKeyExpr(self, ctx: AssetSelectionParser.KeyExprContext):
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

    # Visit a parse tree produced by AssetSelectionParser#StatusAttributeExpr.
    def visitStatusAttributeExpr(self, ctx: AssetSelectionParser.StatusAttributeExprContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#ColumnAttributeExpr.
    def visitColumnAttributeExpr(self, ctx: AssetSelectionParser.ColumnAttributeExprContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#TableNameAttributeExpr.
    def visitTableNameAttributeExpr(self, ctx: AssetSelectionParser.TableNameAttributeExprContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#ColumnTagAttributeExpr.
    def visitColumnTagAttributeExpr(self, ctx: AssetSelectionParser.ColumnTagAttributeExprContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#CodeLocationAttributeExpr.
    def visitCodeLocationAttributeExpr(
        self, ctx: AssetSelectionParser.CodeLocationAttributeExprContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#ChangedInBranchAttributeExpr.
    def visitChangedInBranchAttributeExpr(
        self, ctx: AssetSelectionParser.ChangedInBranchAttributeExprContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#value.
    def visitValue(self, ctx: AssetSelectionParser.ValueContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#keyValue.
    def visitKeyValue(self, ctx: AssetSelectionParser.KeyValueContext):
        return self.visitChildren(ctx)


del AssetSelectionParser
