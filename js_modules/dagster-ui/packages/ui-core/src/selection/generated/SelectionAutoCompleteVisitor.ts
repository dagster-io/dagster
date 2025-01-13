// Generated from /Users/marcosalazar/code/dagster/js_modules/dagster-ui/packages/ui-core/src/selection/SelectionAutoComplete.g4 by ANTLR 4.9.0-SNAPSHOT

import {ParseTreeVisitor} from 'antlr4ts/tree/ParseTreeVisitor';

import {
  AllExpressionContext,
  AndExpressionContext,
  AndTokenContext,
  AttributeExpressionContext,
  AttributeNameContext,
  AttributeValueContext,
  AttributeValueWhitespaceContext,
  ColonTokenContext,
  DownTraversalContext,
  DownTraversalExprContext,
  DownTraversalExpressionContext,
  DownTraversalTokenContext,
  ExprContext,
  ExpressionLessParenthesizedExprContext,
  ExpressionlessFunctionExpressionContext,
  ExpressionlessParenthesizedExpressionContext,
  ExpressionlessParenthesizedExpressionWrapperContext,
  FunctionCallExpressionContext,
  FunctionNameContext,
  IncompleteAndExpressionContext,
  IncompleteAttributeExpressionMissingKeyContext,
  IncompleteAttributeExpressionMissingSecondValueContext,
  IncompleteAttributeExpressionMissingValueContext,
  IncompleteExprContext,
  IncompleteExpressionContext,
  IncompleteLeftQuotedStringValueContext,
  IncompleteNotExpressionContext,
  IncompleteOrExpressionContext,
  IncompletePlusTraversalExpressionContext,
  IncompleteRightQuotedStringValueContext,
  LeftParenTokenContext,
  NotExpressionContext,
  NotTokenContext,
  OrExpressionContext,
  OrTokenContext,
  ParenthesizedExprContext,
  ParenthesizedExpressionContext,
  PostAttributeValueWhitespaceContext,
  PostDownwardTraversalWhitespaceContext,
  PostExpressionWhitespaceContext,
  PostLogicalOperatorWhitespaceContext,
  PostNeighborTraversalWhitespaceContext,
  PostNotOperatorWhitespaceContext,
  PostUpwardTraversalWhitespaceContext,
  QuotedStringValueContext,
  RightParenTokenContext,
  StartContext,
  TraversalAllowedExprContext,
  TraversalAllowedExpressionContext,
  TraversalAllowedParenthesizedExpressionContext,
  UnclosedExpressionlessFunctionExpressionContext,
  UnclosedExpressionlessParenthesizedExpressionContext,
  UnclosedFunctionExpressionContext,
  UnclosedParenthesizedExpressionContext,
  UnmatchedValueContext,
  UnquotedStringValueContext,
  UpAndDownTraversalExpressionContext,
  UpTraversalContext,
  UpTraversalExprContext,
  UpTraversalExpressionContext,
  UpTraversalTokenContext,
  ValueContext,
} from './SelectionAutoCompleteParser';

/**
 * This interface defines a complete generic visitor for a parse tree produced
 * by `SelectionAutoCompleteParser`.
 *
 * @param <Result> The return type of the visit operation. Use `void` for
 * operations with no return type.
 */
export interface SelectionAutoCompleteVisitor<Result> extends ParseTreeVisitor<Result> {
  /**
   * Visit a parse tree produced by the `AttributeExpression`
   * labeled alternative in `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAttributeExpression?: (ctx: AttributeExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `FunctionCallExpression`
   * labeled alternative in `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitFunctionCallExpression?: (ctx: FunctionCallExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `TraversalAllowedParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitTraversalAllowedParenthesizedExpression?: (
    ctx: TraversalAllowedParenthesizedExpressionContext,
  ) => Result;

  /**
   * Visit a parse tree produced by the `IncompleteExpression`
   * labeled alternative in `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitIncompleteExpression?: (ctx: IncompleteExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `UpTraversal`
   * labeled alternative in `SelectionAutoCompleteParser.upTraversalExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUpTraversal?: (ctx: UpTraversalContext) => Result;

  /**
   * Visit a parse tree produced by the `ParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.parenthesizedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitParenthesizedExpression?: (ctx: ParenthesizedExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `TraversalAllowedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitTraversalAllowedExpression?: (ctx: TraversalAllowedExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `UpAndDownTraversalExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUpAndDownTraversalExpression?: (ctx: UpAndDownTraversalExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `UpTraversalExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUpTraversalExpression?: (ctx: UpTraversalExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `DownTraversalExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitDownTraversalExpression?: (ctx: DownTraversalExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `NotExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitNotExpression?: (ctx: NotExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `AndExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAndExpression?: (ctx: AndExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `OrExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitOrExpression?: (ctx: OrExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `IncompleteAndExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitIncompleteAndExpression?: (ctx: IncompleteAndExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `IncompleteOrExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitIncompleteOrExpression?: (ctx: IncompleteOrExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `IncompleteNotExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitIncompleteNotExpression?: (ctx: IncompleteNotExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `AllExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAllExpression?: (ctx: AllExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `UnmatchedValue`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUnmatchedValue?: (ctx: UnmatchedValueContext) => Result;

  /**
   * Visit a parse tree produced by the `ExpressionlessParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expressionLessParenthesizedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitExpressionlessParenthesizedExpression?: (
    ctx: ExpressionlessParenthesizedExpressionContext,
  ) => Result;

  /**
   * Visit a parse tree produced by the `DownTraversal`
   * labeled alternative in `SelectionAutoCompleteParser.downTraversalExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitDownTraversal?: (ctx: DownTraversalContext) => Result;

  /**
   * Visit a parse tree produced by the `QuotedStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitQuotedStringValue?: (ctx: QuotedStringValueContext) => Result;

  /**
   * Visit a parse tree produced by the `IncompleteLeftQuotedStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitIncompleteLeftQuotedStringValue?: (ctx: IncompleteLeftQuotedStringValueContext) => Result;

  /**
   * Visit a parse tree produced by the `IncompleteRightQuotedStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitIncompleteRightQuotedStringValue?: (ctx: IncompleteRightQuotedStringValueContext) => Result;

  /**
   * Visit a parse tree produced by the `UnquotedStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUnquotedStringValue?: (ctx: UnquotedStringValueContext) => Result;

  /**
   * Visit a parse tree produced by the `IncompleteAttributeExpressionMissingValue`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitIncompleteAttributeExpressionMissingValue?: (
    ctx: IncompleteAttributeExpressionMissingValueContext,
  ) => Result;

  /**
   * Visit a parse tree produced by the `IncompleteAttributeExpressionMissingSecondValue`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitIncompleteAttributeExpressionMissingSecondValue?: (
    ctx: IncompleteAttributeExpressionMissingSecondValueContext,
  ) => Result;

  /**
   * Visit a parse tree produced by the `ExpressionlessFunctionExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitExpressionlessFunctionExpression?: (ctx: ExpressionlessFunctionExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `UnclosedExpressionlessFunctionExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUnclosedExpressionlessFunctionExpression?: (
    ctx: UnclosedExpressionlessFunctionExpressionContext,
  ) => Result;

  /**
   * Visit a parse tree produced by the `UnclosedFunctionExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUnclosedFunctionExpression?: (ctx: UnclosedFunctionExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `UnclosedParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUnclosedParenthesizedExpression?: (ctx: UnclosedParenthesizedExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `ExpressionlessParenthesizedExpressionWrapper`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitExpressionlessParenthesizedExpressionWrapper?: (
    ctx: ExpressionlessParenthesizedExpressionWrapperContext,
  ) => Result;

  /**
   * Visit a parse tree produced by the `UnclosedExpressionlessParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUnclosedExpressionlessParenthesizedExpression?: (
    ctx: UnclosedExpressionlessParenthesizedExpressionContext,
  ) => Result;

  /**
   * Visit a parse tree produced by the `IncompletePlusTraversalExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitIncompletePlusTraversalExpression?: (
    ctx: IncompletePlusTraversalExpressionContext,
  ) => Result;

  /**
   * Visit a parse tree produced by the `IncompleteAttributeExpressionMissingKey`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitIncompleteAttributeExpressionMissingKey?: (
    ctx: IncompleteAttributeExpressionMissingKeyContext,
  ) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.start`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitStart?: (ctx: StartContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitExpr?: (ctx: ExprContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitTraversalAllowedExpr?: (ctx: TraversalAllowedExprContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.parenthesizedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitParenthesizedExpr?: (ctx: ParenthesizedExprContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitIncompleteExpr?: (ctx: IncompleteExprContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.expressionLessParenthesizedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitExpressionLessParenthesizedExpr?: (ctx: ExpressionLessParenthesizedExprContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.upTraversalExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUpTraversalExpr?: (ctx: UpTraversalExprContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.downTraversalExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitDownTraversalExpr?: (ctx: DownTraversalExprContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.upTraversalToken`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUpTraversalToken?: (ctx: UpTraversalTokenContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.downTraversalToken`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitDownTraversalToken?: (ctx: DownTraversalTokenContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.attributeName`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAttributeName?: (ctx: AttributeNameContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.attributeValue`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAttributeValue?: (ctx: AttributeValueContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.functionName`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitFunctionName?: (ctx: FunctionNameContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.orToken`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitOrToken?: (ctx: OrTokenContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.andToken`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAndToken?: (ctx: AndTokenContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.notToken`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitNotToken?: (ctx: NotTokenContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.colonToken`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitColonToken?: (ctx: ColonTokenContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.leftParenToken`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitLeftParenToken?: (ctx: LeftParenTokenContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.rightParenToken`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitRightParenToken?: (ctx: RightParenTokenContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.attributeValueWhitespace`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAttributeValueWhitespace?: (ctx: AttributeValueWhitespaceContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.postAttributeValueWhitespace`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitPostAttributeValueWhitespace?: (ctx: PostAttributeValueWhitespaceContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.postExpressionWhitespace`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitPostExpressionWhitespace?: (ctx: PostExpressionWhitespaceContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.postNotOperatorWhitespace`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitPostNotOperatorWhitespace?: (ctx: PostNotOperatorWhitespaceContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.postLogicalOperatorWhitespace`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitPostLogicalOperatorWhitespace?: (ctx: PostLogicalOperatorWhitespaceContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.postNeighborTraversalWhitespace`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitPostNeighborTraversalWhitespace?: (ctx: PostNeighborTraversalWhitespaceContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.postUpwardTraversalWhitespace`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitPostUpwardTraversalWhitespace?: (ctx: PostUpwardTraversalWhitespaceContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.postDownwardTraversalWhitespace`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitPostDownwardTraversalWhitespace?: (ctx: PostDownwardTraversalWhitespaceContext) => Result;

  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitValue?: (ctx: ValueContext) => Result;
}
