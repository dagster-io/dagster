// Generated from /Users/marcosalazar/code/dagster/js_modules/dagster-ui/packages/ui-core/src/run-selection/RunSelection.g4 by ANTLR 4.9.0-SNAPSHOT

import {ParseTreeListener} from 'antlr4ts/tree/ParseTreeListener';

import {
  AllExpressionContext,
  AndExpressionContext,
  AttributeExprContext,
  AttributeExpressionContext,
  DownTraversalContext,
  DownTraversalExpressionContext,
  ExprContext,
  FunctionCallExpressionContext,
  FunctionNameContext,
  NameExprContext,
  NameSubstringExprContext,
  NotExpressionContext,
  OrExpressionContext,
  ParenthesizedExpressionContext,
  StartContext,
  StatusAttributeExprContext,
  TraversalAllowedExprContext,
  TraversalAllowedExpressionContext,
  UpAndDownTraversalExpressionContext,
  UpTraversalContext,
  UpTraversalExpressionContext,
  ValueContext,
} from './RunSelectionParser';

/**
 * This interface defines a complete listener for a parse tree produced by
 * `RunSelectionParser`.
 */
export interface RunSelectionListener extends ParseTreeListener {
  /**
   * Enter a parse tree produced by the `TraversalAllowedExpression`
   * labeled alternative in `RunSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterTraversalAllowedExpression?: (ctx: TraversalAllowedExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `TraversalAllowedExpression`
   * labeled alternative in `RunSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitTraversalAllowedExpression?: (ctx: TraversalAllowedExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `UpAndDownTraversalExpression`
   * labeled alternative in `RunSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterUpAndDownTraversalExpression?: (ctx: UpAndDownTraversalExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `UpAndDownTraversalExpression`
   * labeled alternative in `RunSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitUpAndDownTraversalExpression?: (ctx: UpAndDownTraversalExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `UpTraversalExpression`
   * labeled alternative in `RunSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterUpTraversalExpression?: (ctx: UpTraversalExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `UpTraversalExpression`
   * labeled alternative in `RunSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitUpTraversalExpression?: (ctx: UpTraversalExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `DownTraversalExpression`
   * labeled alternative in `RunSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterDownTraversalExpression?: (ctx: DownTraversalExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `DownTraversalExpression`
   * labeled alternative in `RunSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitDownTraversalExpression?: (ctx: DownTraversalExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `NotExpression`
   * labeled alternative in `RunSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterNotExpression?: (ctx: NotExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `NotExpression`
   * labeled alternative in `RunSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitNotExpression?: (ctx: NotExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `AndExpression`
   * labeled alternative in `RunSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterAndExpression?: (ctx: AndExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `AndExpression`
   * labeled alternative in `RunSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitAndExpression?: (ctx: AndExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `OrExpression`
   * labeled alternative in `RunSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterOrExpression?: (ctx: OrExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `OrExpression`
   * labeled alternative in `RunSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitOrExpression?: (ctx: OrExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `AllExpression`
   * labeled alternative in `RunSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterAllExpression?: (ctx: AllExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `AllExpression`
   * labeled alternative in `RunSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitAllExpression?: (ctx: AllExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `NameExpr`
   * labeled alternative in `RunSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  enterNameExpr?: (ctx: NameExprContext) => void;
  /**
   * Exit a parse tree produced by the `NameExpr`
   * labeled alternative in `RunSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  exitNameExpr?: (ctx: NameExprContext) => void;

  /**
   * Enter a parse tree produced by the `NameSubstringExpr`
   * labeled alternative in `RunSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  enterNameSubstringExpr?: (ctx: NameSubstringExprContext) => void;
  /**
   * Exit a parse tree produced by the `NameSubstringExpr`
   * labeled alternative in `RunSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  exitNameSubstringExpr?: (ctx: NameSubstringExprContext) => void;

  /**
   * Enter a parse tree produced by the `StatusAttributeExpr`
   * labeled alternative in `RunSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  enterStatusAttributeExpr?: (ctx: StatusAttributeExprContext) => void;
  /**
   * Exit a parse tree produced by the `StatusAttributeExpr`
   * labeled alternative in `RunSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  exitStatusAttributeExpr?: (ctx: StatusAttributeExprContext) => void;

  /**
   * Enter a parse tree produced by the `AttributeExpression`
   * labeled alternative in `RunSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  enterAttributeExpression?: (ctx: AttributeExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `AttributeExpression`
   * labeled alternative in `RunSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  exitAttributeExpression?: (ctx: AttributeExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `FunctionCallExpression`
   * labeled alternative in `RunSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  enterFunctionCallExpression?: (ctx: FunctionCallExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `FunctionCallExpression`
   * labeled alternative in `RunSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  exitFunctionCallExpression?: (ctx: FunctionCallExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `ParenthesizedExpression`
   * labeled alternative in `RunSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  enterParenthesizedExpression?: (ctx: ParenthesizedExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `ParenthesizedExpression`
   * labeled alternative in `RunSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  exitParenthesizedExpression?: (ctx: ParenthesizedExpressionContext) => void;

  /**
   * Enter a parse tree produced by `RunSelectionParser.start`.
   * @param ctx the parse tree
   */
  enterStart?: (ctx: StartContext) => void;
  /**
   * Exit a parse tree produced by `RunSelectionParser.start`.
   * @param ctx the parse tree
   */
  exitStart?: (ctx: StartContext) => void;

  /**
   * Enter a parse tree produced by `RunSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterExpr?: (ctx: ExprContext) => void;
  /**
   * Exit a parse tree produced by `RunSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitExpr?: (ctx: ExprContext) => void;

  /**
   * Enter a parse tree produced by `RunSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  enterTraversalAllowedExpr?: (ctx: TraversalAllowedExprContext) => void;
  /**
   * Exit a parse tree produced by `RunSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  exitTraversalAllowedExpr?: (ctx: TraversalAllowedExprContext) => void;

  /**
   * Enter a parse tree produced by `RunSelectionParser.upTraversal`.
   * @param ctx the parse tree
   */
  enterUpTraversal?: (ctx: UpTraversalContext) => void;
  /**
   * Exit a parse tree produced by `RunSelectionParser.upTraversal`.
   * @param ctx the parse tree
   */
  exitUpTraversal?: (ctx: UpTraversalContext) => void;

  /**
   * Enter a parse tree produced by `RunSelectionParser.downTraversal`.
   * @param ctx the parse tree
   */
  enterDownTraversal?: (ctx: DownTraversalContext) => void;
  /**
   * Exit a parse tree produced by `RunSelectionParser.downTraversal`.
   * @param ctx the parse tree
   */
  exitDownTraversal?: (ctx: DownTraversalContext) => void;

  /**
   * Enter a parse tree produced by `RunSelectionParser.functionName`.
   * @param ctx the parse tree
   */
  enterFunctionName?: (ctx: FunctionNameContext) => void;
  /**
   * Exit a parse tree produced by `RunSelectionParser.functionName`.
   * @param ctx the parse tree
   */
  exitFunctionName?: (ctx: FunctionNameContext) => void;

  /**
   * Enter a parse tree produced by `RunSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  enterAttributeExpr?: (ctx: AttributeExprContext) => void;
  /**
   * Exit a parse tree produced by `RunSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  exitAttributeExpr?: (ctx: AttributeExprContext) => void;

  /**
   * Enter a parse tree produced by `RunSelectionParser.value`.
   * @param ctx the parse tree
   */
  enterValue?: (ctx: ValueContext) => void;
  /**
   * Exit a parse tree produced by `RunSelectionParser.value`.
   * @param ctx the parse tree
   */
  exitValue?: (ctx: ValueContext) => void;
}
