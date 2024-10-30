# Generated from AssetSelection.g4 by ANTLR 4.13.2
from antlr4 import *

if "." in __name__:
    from .AssetSelectionParser import AssetSelectionParser
else:
    from AssetSelectionParser import AssetSelectionParser

# This class defines a complete generic visitor for a parse tree produced by AssetSelectionParser.


class AssetSelectionVisitor(ParseTreeVisitor):
    # Visit a parse tree produced by AssetSelectionParser#AndExpression.
    def visitAndExpression(self, ctx: AssetSelectionParser.AndExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#ToPrimaryExpression.
    def visitToPrimaryExpression(self, ctx: AssetSelectionParser.ToPrimaryExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#NotExpression.
    def visitNotExpression(self, ctx: AssetSelectionParser.NotExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#OrExpression.
    def visitOrExpression(self, ctx: AssetSelectionParser.OrExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#KeyValueExpressionWithTraversal.
    def visitKeyValueExpressionWithTraversal(
        self, ctx: AssetSelectionParser.KeyValueExpressionWithTraversalContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#AssetExpressionWithTraversal.
    def visitAssetExpressionWithTraversal(
        self, ctx: AssetSelectionParser.AssetExpressionWithTraversalContext
    ):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#ParenthesizedExpressionWithTraversal.
    def visitParenthesizedExpressionWithTraversal(
        self, ctx: AssetSelectionParser.ParenthesizedExpressionWithTraversalContext
    ):
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

    # Visit a parse tree produced by AssetSelectionParser#arguments.
    def visitArguments(self, ctx: AssetSelectionParser.ArgumentsContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#ExactMatchAsset.
    def visitExactMatchAsset(self, ctx: AssetSelectionParser.ExactMatchAssetContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by AssetSelectionParser#PrefixMatchAsset.
    def visitPrefixMatchAsset(self, ctx: AssetSelectionParser.PrefixMatchAssetContext):
        return self.visitChildren(ctx)


del AssetSelectionParser
