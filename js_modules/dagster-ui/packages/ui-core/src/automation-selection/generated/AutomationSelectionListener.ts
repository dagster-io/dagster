// Generated from /Users/salazarm/code/dagster/js_modules/dagster-ui/packages/ui-core/src/automation-selection/AutomationSelection.g4 by ANTLR 4.9.0-SNAPSHOT

import {ParseTreeListener} from 'antlr4ts/tree/ParseTreeListener';

import {
  AllExpressionContext,
  AndExpressionContext,
  AttributeExprContext,
  AttributeExpressionContext,
  CodeLocationExprContext,
  ExprContext,
  KeyValueContext,
  NameExprContext,
  NotExpressionContext,
  OrExpressionContext,
  ParenthesizedExpressionContext,
  StartContext,
  StatusExprContext,
  TagExprContext,
  TraversalAllowedExprContext,
  TraversalAllowedExpressionContext,
  TypeExprContext,
  ValueContext,
} from './AutomationSelectionParser';

/**
 * This interface defines a complete listener for a parse tree produced by
 * `AutomationSelectionParser`.
 */
export interface AutomationSelectionListener extends ParseTreeListener {
  /**
   * Enter a parse tree produced by the `TraversalAllowedExpression`
   * labeled alternative in `AutomationSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterTraversalAllowedExpression?: (ctx: TraversalAllowedExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `TraversalAllowedExpression`
   * labeled alternative in `AutomationSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitTraversalAllowedExpression?: (ctx: TraversalAllowedExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `NotExpression`
   * labeled alternative in `AutomationSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterNotExpression?: (ctx: NotExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `NotExpression`
   * labeled alternative in `AutomationSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitNotExpression?: (ctx: NotExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `AndExpression`
   * labeled alternative in `AutomationSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterAndExpression?: (ctx: AndExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `AndExpression`
   * labeled alternative in `AutomationSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitAndExpression?: (ctx: AndExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `OrExpression`
   * labeled alternative in `AutomationSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterOrExpression?: (ctx: OrExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `OrExpression`
   * labeled alternative in `AutomationSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitOrExpression?: (ctx: OrExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `AllExpression`
   * labeled alternative in `AutomationSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterAllExpression?: (ctx: AllExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `AllExpression`
   * labeled alternative in `AutomationSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitAllExpression?: (ctx: AllExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `NameExpr`
   * labeled alternative in `AutomationSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  enterNameExpr?: (ctx: NameExprContext) => void;
  /**
   * Exit a parse tree produced by the `NameExpr`
   * labeled alternative in `AutomationSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  exitNameExpr?: (ctx: NameExprContext) => void;

  /**
   * Enter a parse tree produced by the `TagExpr`
   * labeled alternative in `AutomationSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  enterTagExpr?: (ctx: TagExprContext) => void;
  /**
   * Exit a parse tree produced by the `TagExpr`
   * labeled alternative in `AutomationSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  exitTagExpr?: (ctx: TagExprContext) => void;

  /**
   * Enter a parse tree produced by the `TypeExpr`
   * labeled alternative in `AutomationSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  enterTypeExpr?: (ctx: TypeExprContext) => void;
  /**
   * Exit a parse tree produced by the `TypeExpr`
   * labeled alternative in `AutomationSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  exitTypeExpr?: (ctx: TypeExprContext) => void;

  /**
   * Enter a parse tree produced by the `StatusExpr`
   * labeled alternative in `AutomationSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  enterStatusExpr?: (ctx: StatusExprContext) => void;
  /**
   * Exit a parse tree produced by the `StatusExpr`
   * labeled alternative in `AutomationSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  exitStatusExpr?: (ctx: StatusExprContext) => void;

  /**
   * Enter a parse tree produced by the `CodeLocationExpr`
   * labeled alternative in `AutomationSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  enterCodeLocationExpr?: (ctx: CodeLocationExprContext) => void;
  /**
   * Exit a parse tree produced by the `CodeLocationExpr`
   * labeled alternative in `AutomationSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  exitCodeLocationExpr?: (ctx: CodeLocationExprContext) => void;

  /**
   * Enter a parse tree produced by the `AttributeExpression`
   * labeled alternative in `AutomationSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  enterAttributeExpression?: (ctx: AttributeExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `AttributeExpression`
   * labeled alternative in `AutomationSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  exitAttributeExpression?: (ctx: AttributeExpressionContext) => void;

  /**
   * Enter a parse tree produced by the `ParenthesizedExpression`
   * labeled alternative in `AutomationSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  enterParenthesizedExpression?: (ctx: ParenthesizedExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `ParenthesizedExpression`
   * labeled alternative in `AutomationSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  exitParenthesizedExpression?: (ctx: ParenthesizedExpressionContext) => void;

  /**
   * Enter a parse tree produced by `AutomationSelectionParser.start`.
   * @param ctx the parse tree
   */
  enterStart?: (ctx: StartContext) => void;
  /**
   * Exit a parse tree produced by `AutomationSelectionParser.start`.
   * @param ctx the parse tree
   */
  exitStart?: (ctx: StartContext) => void;

  /**
   * Enter a parse tree produced by `AutomationSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterExpr?: (ctx: ExprContext) => void;
  /**
   * Exit a parse tree produced by `AutomationSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitExpr?: (ctx: ExprContext) => void;

  /**
   * Enter a parse tree produced by `AutomationSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  enterTraversalAllowedExpr?: (ctx: TraversalAllowedExprContext) => void;
  /**
   * Exit a parse tree produced by `AutomationSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  exitTraversalAllowedExpr?: (ctx: TraversalAllowedExprContext) => void;

  /**
   * Enter a parse tree produced by `AutomationSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  enterAttributeExpr?: (ctx: AttributeExprContext) => void;
  /**
   * Exit a parse tree produced by `AutomationSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  exitAttributeExpr?: (ctx: AttributeExprContext) => void;

  /**
   * Enter a parse tree produced by `AutomationSelectionParser.value`.
   * @param ctx the parse tree
   */
  enterValue?: (ctx: ValueContext) => void;
  /**
   * Exit a parse tree produced by `AutomationSelectionParser.value`.
   * @param ctx the parse tree
   */
  exitValue?: (ctx: ValueContext) => void;

  /**
   * Enter a parse tree produced by `AutomationSelectionParser.keyValue`.
   * @param ctx the parse tree
   */
  enterKeyValue?: (ctx: KeyValueContext) => void;
  /**
   * Exit a parse tree produced by `AutomationSelectionParser.keyValue`.
   * @param ctx the parse tree
   */
  exitKeyValue?: (ctx: KeyValueContext) => void;
}
