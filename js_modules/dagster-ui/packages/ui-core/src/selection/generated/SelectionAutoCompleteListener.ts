// Generated from /Users/marcosalazar/code/dagster/js_modules/dagster-ui/packages/ui-core/src/selection/SelectionAutoComplete.g4 by ANTLR 4.9.0-SNAPSHOT

import {ParseTreeListener} from 'antlr4ts/tree/ParseTreeListener';

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
 * This interface defines a complete listener for a parse tree produced by
 * `SelectionAutoCompleteParser`.
 */
export interface SelectionAutoCompleteListener extends ParseTreeListener {
  /**
   * Enter a parse tree produced by the `AttributeExpression`
   * labeled alternative in `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  enterAttributeExpression?: (ctx: AttributeExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `AttributeExpression`
   * labeled alternative in `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  exitAttributeExpression?: (ctx: AttributeExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `FunctionCallExpression`
   * labeled alternative in `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  enterFunctionCallExpression?: (ctx: FunctionCallExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `FunctionCallExpression`
   * labeled alternative in `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  exitFunctionCallExpression?: (ctx: FunctionCallExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `TraversalAllowedParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  enterTraversalAllowedParenthesizedExpression?: (
    ctx: TraversalAllowedParenthesizedExpressionContext,
  ) => void;
  /**
   * Exit a parse tree produced by the `TraversalAllowedParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  exitTraversalAllowedParenthesizedExpression?: (
    ctx: TraversalAllowedParenthesizedExpressionContext,
  ) => void;

  /**
   * Enter a parse tree produced by the `IncompleteExpression`
   * labeled alternative in `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  enterIncompleteExpression?: (ctx: IncompleteExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `IncompleteExpression`
   * labeled alternative in `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  exitIncompleteExpression?: (ctx: IncompleteExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `UpTraversal`
   * labeled alternative in `SelectionAutoCompleteParser.upTraversalExpr`.
   * @param ctx the parse tree
   */
  enterUpTraversal?: (ctx: UpTraversalContext) => void;
  /**
   * Exit a parse tree produced by the `UpTraversal`
   * labeled alternative in `SelectionAutoCompleteParser.upTraversalExpr`.
   * @param ctx the parse tree
   */
  exitUpTraversal?: (ctx: UpTraversalContext) => void;

  /**
   * Enter a parse tree produced by the `ParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.parenthesizedExpr`.
   * @param ctx the parse tree
   */
  enterParenthesizedExpression?: (ctx: ParenthesizedExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `ParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.parenthesizedExpr`.
   * @param ctx the parse tree
   */
  exitParenthesizedExpression?: (ctx: ParenthesizedExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `TraversalAllowedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterTraversalAllowedExpression?: (ctx: TraversalAllowedExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `TraversalAllowedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitTraversalAllowedExpression?: (ctx: TraversalAllowedExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `UpAndDownTraversalExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterUpAndDownTraversalExpression?: (ctx: UpAndDownTraversalExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `UpAndDownTraversalExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitUpAndDownTraversalExpression?: (ctx: UpAndDownTraversalExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `UpTraversalExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterUpTraversalExpression?: (ctx: UpTraversalExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `UpTraversalExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitUpTraversalExpression?: (ctx: UpTraversalExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `DownTraversalExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterDownTraversalExpression?: (ctx: DownTraversalExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `DownTraversalExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitDownTraversalExpression?: (ctx: DownTraversalExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `NotExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterNotExpression?: (ctx: NotExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `NotExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitNotExpression?: (ctx: NotExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `AndExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterAndExpression?: (ctx: AndExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `AndExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitAndExpression?: (ctx: AndExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `OrExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterOrExpression?: (ctx: OrExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `OrExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitOrExpression?: (ctx: OrExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `IncompleteAndExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterIncompleteAndExpression?: (ctx: IncompleteAndExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `IncompleteAndExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitIncompleteAndExpression?: (ctx: IncompleteAndExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `IncompleteOrExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterIncompleteOrExpression?: (ctx: IncompleteOrExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `IncompleteOrExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitIncompleteOrExpression?: (ctx: IncompleteOrExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `IncompleteNotExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterIncompleteNotExpression?: (ctx: IncompleteNotExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `IncompleteNotExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitIncompleteNotExpression?: (ctx: IncompleteNotExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `AllExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterAllExpression?: (ctx: AllExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `AllExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitAllExpression?: (ctx: AllExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `UnmatchedValue`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterUnmatchedValue?: (ctx: UnmatchedValueContext) => void;
  /**
   * Exit a parse tree produced by the `UnmatchedValue`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitUnmatchedValue?: (ctx: UnmatchedValueContext) => void;

  /**
   * Enter a parse tree produced by the `ExpressionlessParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expressionLessParenthesizedExpr`.
   * @param ctx the parse tree
   */
  enterExpressionlessParenthesizedExpression?: (
    ctx: ExpressionlessParenthesizedExpressionContext,
  ) => void;
  /**
   * Exit a parse tree produced by the `ExpressionlessParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expressionLessParenthesizedExpr`.
   * @param ctx the parse tree
   */
  exitExpressionlessParenthesizedExpression?: (
    ctx: ExpressionlessParenthesizedExpressionContext,
  ) => void;

  /**
   * Enter a parse tree produced by the `DownTraversal`
   * labeled alternative in `SelectionAutoCompleteParser.downTraversalExpr`.
   * @param ctx the parse tree
   */
  enterDownTraversal?: (ctx: DownTraversalContext) => void;
  /**
   * Exit a parse tree produced by the `DownTraversal`
   * labeled alternative in `SelectionAutoCompleteParser.downTraversalExpr`.
   * @param ctx the parse tree
   */
  exitDownTraversal?: (ctx: DownTraversalContext) => void;

  /**
   * Enter a parse tree produced by the `QuotedStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   */
  enterQuotedStringValue?: (ctx: QuotedStringValueContext) => void;
  /**
   * Exit a parse tree produced by the `QuotedStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   */
  exitQuotedStringValue?: (ctx: QuotedStringValueContext) => void;

  /**
   * Enter a parse tree produced by the `IncompleteLeftQuotedStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   */
  enterIncompleteLeftQuotedStringValue?: (ctx: IncompleteLeftQuotedStringValueContext) => void;
  /**
   * Exit a parse tree produced by the `IncompleteLeftQuotedStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   */
  exitIncompleteLeftQuotedStringValue?: (ctx: IncompleteLeftQuotedStringValueContext) => void;

  /**
   * Enter a parse tree produced by the `IncompleteRightQuotedStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   */
  enterIncompleteRightQuotedStringValue?: (ctx: IncompleteRightQuotedStringValueContext) => void;
  /**
   * Exit a parse tree produced by the `IncompleteRightQuotedStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   */
  exitIncompleteRightQuotedStringValue?: (ctx: IncompleteRightQuotedStringValueContext) => void;

  /**
   * Enter a parse tree produced by the `UnquotedStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   */
  enterUnquotedStringValue?: (ctx: UnquotedStringValueContext) => void;
  /**
   * Exit a parse tree produced by the `UnquotedStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   */
  exitUnquotedStringValue?: (ctx: UnquotedStringValueContext) => void;

  /**
   * Enter a parse tree produced by the `IncompleteAttributeExpressionMissingValue`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  enterIncompleteAttributeExpressionMissingValue?: (
    ctx: IncompleteAttributeExpressionMissingValueContext,
  ) => void;
  /**
   * Exit a parse tree produced by the `IncompleteAttributeExpressionMissingValue`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  exitIncompleteAttributeExpressionMissingValue?: (
    ctx: IncompleteAttributeExpressionMissingValueContext,
  ) => void;

  /**
   * Enter a parse tree produced by the `IncompleteAttributeExpressionMissingSecondValue`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  enterIncompleteAttributeExpressionMissingSecondValue?: (
    ctx: IncompleteAttributeExpressionMissingSecondValueContext,
  ) => void;
  /**
   * Exit a parse tree produced by the `IncompleteAttributeExpressionMissingSecondValue`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  exitIncompleteAttributeExpressionMissingSecondValue?: (
    ctx: IncompleteAttributeExpressionMissingSecondValueContext,
  ) => void;

  /**
   * Enter a parse tree produced by the `ExpressionlessFunctionExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  enterExpressionlessFunctionExpression?: (ctx: ExpressionlessFunctionExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `ExpressionlessFunctionExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  exitExpressionlessFunctionExpression?: (ctx: ExpressionlessFunctionExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `UnclosedExpressionlessFunctionExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  enterUnclosedExpressionlessFunctionExpression?: (
    ctx: UnclosedExpressionlessFunctionExpressionContext,
  ) => void;
  /**
   * Exit a parse tree produced by the `UnclosedExpressionlessFunctionExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  exitUnclosedExpressionlessFunctionExpression?: (
    ctx: UnclosedExpressionlessFunctionExpressionContext,
  ) => void;

  /**
   * Enter a parse tree produced by the `UnclosedFunctionExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  enterUnclosedFunctionExpression?: (ctx: UnclosedFunctionExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `UnclosedFunctionExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  exitUnclosedFunctionExpression?: (ctx: UnclosedFunctionExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `UnclosedParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  enterUnclosedParenthesizedExpression?: (ctx: UnclosedParenthesizedExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `UnclosedParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  exitUnclosedParenthesizedExpression?: (ctx: UnclosedParenthesizedExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `ExpressionlessParenthesizedExpressionWrapper`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  enterExpressionlessParenthesizedExpressionWrapper?: (
    ctx: ExpressionlessParenthesizedExpressionWrapperContext,
  ) => void;
  /**
   * Exit a parse tree produced by the `ExpressionlessParenthesizedExpressionWrapper`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  exitExpressionlessParenthesizedExpressionWrapper?: (
    ctx: ExpressionlessParenthesizedExpressionWrapperContext,
  ) => void;

  /**
   * Enter a parse tree produced by the `UnclosedExpressionlessParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  enterUnclosedExpressionlessParenthesizedExpression?: (
    ctx: UnclosedExpressionlessParenthesizedExpressionContext,
  ) => void;
  /**
   * Exit a parse tree produced by the `UnclosedExpressionlessParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  exitUnclosedExpressionlessParenthesizedExpression?: (
    ctx: UnclosedExpressionlessParenthesizedExpressionContext,
  ) => void;

  /**
   * Enter a parse tree produced by the `IncompletePlusTraversalExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  enterIncompletePlusTraversalExpression?: (ctx: IncompletePlusTraversalExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `IncompletePlusTraversalExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  exitIncompletePlusTraversalExpression?: (ctx: IncompletePlusTraversalExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `IncompleteAttributeExpressionMissingKey`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  enterIncompleteAttributeExpressionMissingKey?: (
    ctx: IncompleteAttributeExpressionMissingKeyContext,
  ) => void;
  /**
   * Exit a parse tree produced by the `IncompleteAttributeExpressionMissingKey`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  exitIncompleteAttributeExpressionMissingKey?: (
    ctx: IncompleteAttributeExpressionMissingKeyContext,
  ) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.start`.
   * @param ctx the parse tree
   */
  enterStart?: (ctx: StartContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.start`.
   * @param ctx the parse tree
   */
  exitStart?: (ctx: StartContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterExpr?: (ctx: ExprContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitExpr?: (ctx: ExprContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  enterTraversalAllowedExpr?: (ctx: TraversalAllowedExprContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  exitTraversalAllowedExpr?: (ctx: TraversalAllowedExprContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.parenthesizedExpr`.
   * @param ctx the parse tree
   */
  enterParenthesizedExpr?: (ctx: ParenthesizedExprContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.parenthesizedExpr`.
   * @param ctx the parse tree
   */
  exitParenthesizedExpr?: (ctx: ParenthesizedExprContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  enterIncompleteExpr?: (ctx: IncompleteExprContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  exitIncompleteExpr?: (ctx: IncompleteExprContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.expressionLessParenthesizedExpr`.
   * @param ctx the parse tree
   */
  enterExpressionLessParenthesizedExpr?: (ctx: ExpressionLessParenthesizedExprContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.expressionLessParenthesizedExpr`.
   * @param ctx the parse tree
   */
  exitExpressionLessParenthesizedExpr?: (ctx: ExpressionLessParenthesizedExprContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.upTraversalExpr`.
   * @param ctx the parse tree
   */
  enterUpTraversalExpr?: (ctx: UpTraversalExprContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.upTraversalExpr`.
   * @param ctx the parse tree
   */
  exitUpTraversalExpr?: (ctx: UpTraversalExprContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.downTraversalExpr`.
   * @param ctx the parse tree
   */
  enterDownTraversalExpr?: (ctx: DownTraversalExprContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.downTraversalExpr`.
   * @param ctx the parse tree
   */
  exitDownTraversalExpr?: (ctx: DownTraversalExprContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.upTraversalToken`.
   * @param ctx the parse tree
   */
  enterUpTraversalToken?: (ctx: UpTraversalTokenContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.upTraversalToken`.
   * @param ctx the parse tree
   */
  exitUpTraversalToken?: (ctx: UpTraversalTokenContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.downTraversalToken`.
   * @param ctx the parse tree
   */
  enterDownTraversalToken?: (ctx: DownTraversalTokenContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.downTraversalToken`.
   * @param ctx the parse tree
   */
  exitDownTraversalToken?: (ctx: DownTraversalTokenContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.attributeName`.
   * @param ctx the parse tree
   */
  enterAttributeName?: (ctx: AttributeNameContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.attributeName`.
   * @param ctx the parse tree
   */
  exitAttributeName?: (ctx: AttributeNameContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.attributeValue`.
   * @param ctx the parse tree
   */
  enterAttributeValue?: (ctx: AttributeValueContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.attributeValue`.
   * @param ctx the parse tree
   */
  exitAttributeValue?: (ctx: AttributeValueContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.functionName`.
   * @param ctx the parse tree
   */
  enterFunctionName?: (ctx: FunctionNameContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.functionName`.
   * @param ctx the parse tree
   */
  exitFunctionName?: (ctx: FunctionNameContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.orToken`.
   * @param ctx the parse tree
   */
  enterOrToken?: (ctx: OrTokenContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.orToken`.
   * @param ctx the parse tree
   */
  exitOrToken?: (ctx: OrTokenContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.andToken`.
   * @param ctx the parse tree
   */
  enterAndToken?: (ctx: AndTokenContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.andToken`.
   * @param ctx the parse tree
   */
  exitAndToken?: (ctx: AndTokenContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.notToken`.
   * @param ctx the parse tree
   */
  enterNotToken?: (ctx: NotTokenContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.notToken`.
   * @param ctx the parse tree
   */
  exitNotToken?: (ctx: NotTokenContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.colonToken`.
   * @param ctx the parse tree
   */
  enterColonToken?: (ctx: ColonTokenContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.colonToken`.
   * @param ctx the parse tree
   */
  exitColonToken?: (ctx: ColonTokenContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.leftParenToken`.
   * @param ctx the parse tree
   */
  enterLeftParenToken?: (ctx: LeftParenTokenContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.leftParenToken`.
   * @param ctx the parse tree
   */
  exitLeftParenToken?: (ctx: LeftParenTokenContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.rightParenToken`.
   * @param ctx the parse tree
   */
  enterRightParenToken?: (ctx: RightParenTokenContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.rightParenToken`.
   * @param ctx the parse tree
   */
  exitRightParenToken?: (ctx: RightParenTokenContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.attributeValueWhitespace`.
   * @param ctx the parse tree
   */
  enterAttributeValueWhitespace?: (ctx: AttributeValueWhitespaceContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.attributeValueWhitespace`.
   * @param ctx the parse tree
   */
  exitAttributeValueWhitespace?: (ctx: AttributeValueWhitespaceContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.postAttributeValueWhitespace`.
   * @param ctx the parse tree
   */
  enterPostAttributeValueWhitespace?: (ctx: PostAttributeValueWhitespaceContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.postAttributeValueWhitespace`.
   * @param ctx the parse tree
   */
  exitPostAttributeValueWhitespace?: (ctx: PostAttributeValueWhitespaceContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.postExpressionWhitespace`.
   * @param ctx the parse tree
   */
  enterPostExpressionWhitespace?: (ctx: PostExpressionWhitespaceContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.postExpressionWhitespace`.
   * @param ctx the parse tree
   */
  exitPostExpressionWhitespace?: (ctx: PostExpressionWhitespaceContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.postNotOperatorWhitespace`.
   * @param ctx the parse tree
   */
  enterPostNotOperatorWhitespace?: (ctx: PostNotOperatorWhitespaceContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.postNotOperatorWhitespace`.
   * @param ctx the parse tree
   */
  exitPostNotOperatorWhitespace?: (ctx: PostNotOperatorWhitespaceContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.postLogicalOperatorWhitespace`.
   * @param ctx the parse tree
   */
  enterPostLogicalOperatorWhitespace?: (ctx: PostLogicalOperatorWhitespaceContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.postLogicalOperatorWhitespace`.
   * @param ctx the parse tree
   */
  exitPostLogicalOperatorWhitespace?: (ctx: PostLogicalOperatorWhitespaceContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.postNeighborTraversalWhitespace`.
   * @param ctx the parse tree
   */
  enterPostNeighborTraversalWhitespace?: (ctx: PostNeighborTraversalWhitespaceContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.postNeighborTraversalWhitespace`.
   * @param ctx the parse tree
   */
  exitPostNeighborTraversalWhitespace?: (ctx: PostNeighborTraversalWhitespaceContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.postUpwardTraversalWhitespace`.
   * @param ctx the parse tree
   */
  enterPostUpwardTraversalWhitespace?: (ctx: PostUpwardTraversalWhitespaceContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.postUpwardTraversalWhitespace`.
   * @param ctx the parse tree
   */
  exitPostUpwardTraversalWhitespace?: (ctx: PostUpwardTraversalWhitespaceContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.postDownwardTraversalWhitespace`.
   * @param ctx the parse tree
   */
  enterPostDownwardTraversalWhitespace?: (ctx: PostDownwardTraversalWhitespaceContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.postDownwardTraversalWhitespace`.
   * @param ctx the parse tree
   */
  exitPostDownwardTraversalWhitespace?: (ctx: PostDownwardTraversalWhitespaceContext) => void;

  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   */
  enterValue?: (ctx: ValueContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   */
  exitValue?: (ctx: ValueContext) => void;
}
