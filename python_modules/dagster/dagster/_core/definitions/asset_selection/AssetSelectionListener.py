# Generated from AssetSelection.g4 by ANTLR 4.13.2
from antlr4 import *

if "." in __name__:
    from .AssetSelectionParser import AssetSelectionParser
else:
    from AssetSelectionParser import AssetSelectionParser


# This class defines a complete listener for a parse tree produced by AssetSelectionParser.
class AssetSelectionListener(ParseTreeListener):
    # Enter a parse tree produced by AssetSelectionParser#AndExpression.
    def enterAndExpression(self, ctx: AssetSelectionParser.AndExpressionContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#AndExpression.
    def exitAndExpression(self, ctx: AssetSelectionParser.AndExpressionContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#ToPrimaryExpression.
    def enterToPrimaryExpression(self, ctx: AssetSelectionParser.ToPrimaryExpressionContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#ToPrimaryExpression.
    def exitToPrimaryExpression(self, ctx: AssetSelectionParser.ToPrimaryExpressionContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#NotExpression.
    def enterNotExpression(self, ctx: AssetSelectionParser.NotExpressionContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#NotExpression.
    def exitNotExpression(self, ctx: AssetSelectionParser.NotExpressionContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#OrExpression.
    def enterOrExpression(self, ctx: AssetSelectionParser.OrExpressionContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#OrExpression.
    def exitOrExpression(self, ctx: AssetSelectionParser.OrExpressionContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#KeyValueExpressionWithTraversal.
    def enterKeyValueExpressionWithTraversal(
        self, ctx: AssetSelectionParser.KeyValueExpressionWithTraversalContext
    ):
        pass

    # Exit a parse tree produced by AssetSelectionParser#KeyValueExpressionWithTraversal.
    def exitKeyValueExpressionWithTraversal(
        self, ctx: AssetSelectionParser.KeyValueExpressionWithTraversalContext
    ):
        pass

    # Enter a parse tree produced by AssetSelectionParser#AssetExpressionWithTraversal.
    def enterAssetExpressionWithTraversal(
        self, ctx: AssetSelectionParser.AssetExpressionWithTraversalContext
    ):
        pass

    # Exit a parse tree produced by AssetSelectionParser#AssetExpressionWithTraversal.
    def exitAssetExpressionWithTraversal(
        self, ctx: AssetSelectionParser.AssetExpressionWithTraversalContext
    ):
        pass

    # Enter a parse tree produced by AssetSelectionParser#ParenthesizedExpressionWithTraversal.
    def enterParenthesizedExpressionWithTraversal(
        self, ctx: AssetSelectionParser.ParenthesizedExpressionWithTraversalContext
    ):
        pass

    # Exit a parse tree produced by AssetSelectionParser#ParenthesizedExpressionWithTraversal.
    def exitParenthesizedExpressionWithTraversal(
        self, ctx: AssetSelectionParser.ParenthesizedExpressionWithTraversalContext
    ):
        pass

    # Enter a parse tree produced by AssetSelectionParser#FunctionCallExpression.
    def enterFunctionCallExpression(self, ctx: AssetSelectionParser.FunctionCallExpressionContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#FunctionCallExpression.
    def exitFunctionCallExpression(self, ctx: AssetSelectionParser.FunctionCallExpressionContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#traversal.
    def enterTraversal(self, ctx: AssetSelectionParser.TraversalContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#traversal.
    def exitTraversal(self, ctx: AssetSelectionParser.TraversalContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#functionName.
    def enterFunctionName(self, ctx: AssetSelectionParser.FunctionNameContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#functionName.
    def exitFunctionName(self, ctx: AssetSelectionParser.FunctionNameContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#TagKeyValuePair.
    def enterTagKeyValuePair(self, ctx: AssetSelectionParser.TagKeyValuePairContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#TagKeyValuePair.
    def exitTagKeyValuePair(self, ctx: AssetSelectionParser.TagKeyValuePairContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#OwnerKeyValuePair.
    def enterOwnerKeyValuePair(self, ctx: AssetSelectionParser.OwnerKeyValuePairContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#OwnerKeyValuePair.
    def exitOwnerKeyValuePair(self, ctx: AssetSelectionParser.OwnerKeyValuePairContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#GroupKeyValuePair.
    def enterGroupKeyValuePair(self, ctx: AssetSelectionParser.GroupKeyValuePairContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#GroupKeyValuePair.
    def exitGroupKeyValuePair(self, ctx: AssetSelectionParser.GroupKeyValuePairContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#KindKeyValuePair.
    def enterKindKeyValuePair(self, ctx: AssetSelectionParser.KindKeyValuePairContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#KindKeyValuePair.
    def exitKindKeyValuePair(self, ctx: AssetSelectionParser.KindKeyValuePairContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#RepoKeyValuePair.
    def enterRepoKeyValuePair(self, ctx: AssetSelectionParser.RepoKeyValuePairContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#RepoKeyValuePair.
    def exitRepoKeyValuePair(self, ctx: AssetSelectionParser.RepoKeyValuePairContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#value.
    def enterValue(self, ctx: AssetSelectionParser.ValueContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#value.
    def exitValue(self, ctx: AssetSelectionParser.ValueContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#arguments.
    def enterArguments(self, ctx: AssetSelectionParser.ArgumentsContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#arguments.
    def exitArguments(self, ctx: AssetSelectionParser.ArgumentsContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#ExactMatchAsset.
    def enterExactMatchAsset(self, ctx: AssetSelectionParser.ExactMatchAssetContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#ExactMatchAsset.
    def exitExactMatchAsset(self, ctx: AssetSelectionParser.ExactMatchAssetContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#PrefixMatchAsset.
    def enterPrefixMatchAsset(self, ctx: AssetSelectionParser.PrefixMatchAssetContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#PrefixMatchAsset.
    def exitPrefixMatchAsset(self, ctx: AssetSelectionParser.PrefixMatchAssetContext):
        pass


del AssetSelectionParser
