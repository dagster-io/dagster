# Generated from AssetSelection.g4 by ANTLR 4.13.2
from antlr4 import *

from .AssetSelectionParser import AssetSelectionParser

# This class defines a complete generic visitor for a parse tree produced by AssetSelectionParser.


class AssetSelectionVisitor(ParseTreeVisitor):
    # Visit a parse tree produced by AssetSelectionParser#AssetExpression.
    def visitAssetExpression(self, ctx: AssetSelectionParser.AssetExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#BothTraversalExpression.
    def visitBothTraversalExpression(
        self, ctx: AssetSelectionParser.BothTraversalExpressionContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#ParenthesizedExpression.
    def visitParenthesizedExpression(
        self, ctx: AssetSelectionParser.ParenthesizedExpressionContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#AndExpression.
    def visitAndExpression(self, ctx: AssetSelectionParser.AndExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#RightTraversalExpression.
    def visitRightTraversalExpression(
        self, ctx: AssetSelectionParser.RightTraversalExpressionContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#KeyValueExpression.
    def visitKeyValueExpression(self, ctx: AssetSelectionParser.KeyValueExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#NotExpression.
    def visitNotExpression(self, ctx: AssetSelectionParser.NotExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#LeftTraversalExpression.
    def visitLeftTraversalExpression(
        self, ctx: AssetSelectionParser.LeftTraversalExpressionContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#OrExpression.
    def visitOrExpression(self, ctx: AssetSelectionParser.OrExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#FunctionCallExpression.
    def visitFunctionCallExpression(self, ctx: AssetSelectionParser.FunctionCallExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#traversal.
    def visitTraversal(self, ctx: AssetSelectionParser.TraversalContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#functionName.
    def visitFunctionName(self, ctx: AssetSelectionParser.FunctionNameContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#TagKeyValuePair.
    def visitTagKeyValuePair(self, ctx: AssetSelectionParser.TagKeyValuePairContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#OwnerKeyValuePair.
    def visitOwnerKeyValuePair(self, ctx: AssetSelectionParser.OwnerKeyValuePairContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#GroupKeyValuePair.
    def visitGroupKeyValuePair(self, ctx: AssetSelectionParser.GroupKeyValuePairContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#KindKeyValuePair.
    def visitKindKeyValuePair(self, ctx: AssetSelectionParser.KindKeyValuePairContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#RepoKeyValuePair.
    def visitRepoKeyValuePair(self, ctx: AssetSelectionParser.RepoKeyValuePairContext):
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
