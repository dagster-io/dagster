# flake8: noqa
# type: ignore
# Generated from AssetSelection.g4 by ANTLR 4.13.2
from antlr4 import *
from .AssetSelectionParser import AssetSelectionParser


# This class defines a complete listener for a parse tree produced by AssetSelectionParser.
class AssetSelectionListener(ParseTreeListener):
    # Enter a parse tree produced by AssetSelectionParser#start.
    def enterStart(self, ctx: AssetSelectionParser.StartContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#start.
    def exitStart(self, ctx: AssetSelectionParser.StartContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#UpTraversalExpression.
    def enterUpTraversalExpression(self, ctx: AssetSelectionParser.UpTraversalExpressionContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#UpTraversalExpression.
    def exitUpTraversalExpression(self, ctx: AssetSelectionParser.UpTraversalExpressionContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#AndExpression.
    def enterAndExpression(self, ctx: AssetSelectionParser.AndExpressionContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#AndExpression.
    def exitAndExpression(self, ctx: AssetSelectionParser.AndExpressionContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#AllExpression.
    def enterAllExpression(self, ctx: AssetSelectionParser.AllExpressionContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#AllExpression.
    def exitAllExpression(self, ctx: AssetSelectionParser.AllExpressionContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#TraversalAllowedExpression.
    def enterTraversalAllowedExpression(
        self, ctx: AssetSelectionParser.TraversalAllowedExpressionContext
    ):
        pass

    # Exit a parse tree produced by AssetSelectionParser#TraversalAllowedExpression.
    def exitTraversalAllowedExpression(
        self, ctx: AssetSelectionParser.TraversalAllowedExpressionContext
    ):
        pass

    # Enter a parse tree produced by AssetSelectionParser#DownTraversalExpression.
    def enterDownTraversalExpression(
        self, ctx: AssetSelectionParser.DownTraversalExpressionContext
    ):
        pass

    # Exit a parse tree produced by AssetSelectionParser#DownTraversalExpression.
    def exitDownTraversalExpression(self, ctx: AssetSelectionParser.DownTraversalExpressionContext):
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

    # Enter a parse tree produced by AssetSelectionParser#UpAndDownTraversalExpression.
    def enterUpAndDownTraversalExpression(
        self, ctx: AssetSelectionParser.UpAndDownTraversalExpressionContext
    ):
        pass

    # Exit a parse tree produced by AssetSelectionParser#UpAndDownTraversalExpression.
    def exitUpAndDownTraversalExpression(
        self, ctx: AssetSelectionParser.UpAndDownTraversalExpressionContext
    ):
        pass

    # Enter a parse tree produced by AssetSelectionParser#AttributeExpression.
    def enterAttributeExpression(self, ctx: AssetSelectionParser.AttributeExpressionContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#AttributeExpression.
    def exitAttributeExpression(self, ctx: AssetSelectionParser.AttributeExpressionContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#FunctionCallExpression.
    def enterFunctionCallExpression(self, ctx: AssetSelectionParser.FunctionCallExpressionContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#FunctionCallExpression.
    def exitFunctionCallExpression(self, ctx: AssetSelectionParser.FunctionCallExpressionContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#ParenthesizedExpression.
    def enterParenthesizedExpression(
        self, ctx: AssetSelectionParser.ParenthesizedExpressionContext
    ):
        pass

    # Exit a parse tree produced by AssetSelectionParser#ParenthesizedExpression.
    def exitParenthesizedExpression(self, ctx: AssetSelectionParser.ParenthesizedExpressionContext):
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

    # Enter a parse tree produced by AssetSelectionParser#KeyExpr.
    def enterKeyExpr(self, ctx: AssetSelectionParser.KeyExprContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#KeyExpr.
    def exitKeyExpr(self, ctx: AssetSelectionParser.KeyExprContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#KeySubstringExpr.
    def enterKeySubstringExpr(self, ctx: AssetSelectionParser.KeySubstringExprContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#KeySubstringExpr.
    def exitKeySubstringExpr(self, ctx: AssetSelectionParser.KeySubstringExprContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#TagAttributeExpr.
    def enterTagAttributeExpr(self, ctx: AssetSelectionParser.TagAttributeExprContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#TagAttributeExpr.
    def exitTagAttributeExpr(self, ctx: AssetSelectionParser.TagAttributeExprContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#OwnerAttributeExpr.
    def enterOwnerAttributeExpr(self, ctx: AssetSelectionParser.OwnerAttributeExprContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#OwnerAttributeExpr.
    def exitOwnerAttributeExpr(self, ctx: AssetSelectionParser.OwnerAttributeExprContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#GroupAttributeExpr.
    def enterGroupAttributeExpr(self, ctx: AssetSelectionParser.GroupAttributeExprContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#GroupAttributeExpr.
    def exitGroupAttributeExpr(self, ctx: AssetSelectionParser.GroupAttributeExprContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#KindAttributeExpr.
    def enterKindAttributeExpr(self, ctx: AssetSelectionParser.KindAttributeExprContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#KindAttributeExpr.
    def exitKindAttributeExpr(self, ctx: AssetSelectionParser.KindAttributeExprContext):
        pass

    # Enter a parse tree produced by AssetSelectionParser#CodeLocationAttributeExpr.
    def enterCodeLocationAttributeExpr(
        self, ctx: AssetSelectionParser.CodeLocationAttributeExprContext
    ):
        pass

    # Exit a parse tree produced by AssetSelectionParser#CodeLocationAttributeExpr.
    def exitCodeLocationAttributeExpr(
        self, ctx: AssetSelectionParser.CodeLocationAttributeExprContext
    ):
        pass

    # Enter a parse tree produced by AssetSelectionParser#value.
    def enterValue(self, ctx: AssetSelectionParser.ValueContext):
        pass

    # Exit a parse tree produced by AssetSelectionParser#value.
    def exitValue(self, ctx: AssetSelectionParser.ValueContext):
        pass


del AssetSelectionParser
