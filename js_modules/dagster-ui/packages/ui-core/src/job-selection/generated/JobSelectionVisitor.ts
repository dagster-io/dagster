// Generated from /Users/salazarm/code/dagster/js_modules/dagster-ui/packages/ui-core/src/job-selection/JobSelection.g4 by ANTLR 4.9.0-SNAPSHOT

import {ParseTreeVisitor} from 'antlr4ts/tree/ParseTreeVisitor';

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
  TraversalAllowedExprContext,
  TraversalAllowedExpressionContext,
  ValueContext,
} from './JobSelectionParser';

/**
 * This interface defines a complete generic visitor for a parse tree produced
 * by `JobSelectionParser`.
 *
 * @param <Result> The return type of the visit operation. Use `void` for
 * operations with no return type.
 */
export interface JobSelectionVisitor<Result> extends ParseTreeVisitor<Result> {
  /**
   * Visit a parse tree produced by the `TraversalAllowedExpression`
   * labeled alternative in `JobSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitTraversalAllowedExpression?: (ctx: TraversalAllowedExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `NotExpression`
   * labeled alternative in `JobSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitNotExpression?: (ctx: NotExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `AndExpression`
   * labeled alternative in `JobSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAndExpression?: (ctx: AndExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `OrExpression`
   * labeled alternative in `JobSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitOrExpression?: (ctx: OrExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `AllExpression`
   * labeled alternative in `JobSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAllExpression?: (ctx: AllExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `NameExpr`
   * labeled alternative in `JobSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitNameExpr?: (ctx: NameExprContext) => Result;

  /**
   * Visit a parse tree produced by the `CodeLocationExpr`
   * labeled alternative in `JobSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitCodeLocationExpr?: (ctx: CodeLocationExprContext) => Result;

  /**
   * Visit a parse tree produced by the `AttributeExpression`
   * labeled alternative in `JobSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAttributeExpression?: (ctx: AttributeExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `ParenthesizedExpression`
   * labeled alternative in `JobSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitParenthesizedExpression?: (ctx: ParenthesizedExpressionContext) => Result;

  /**
   * Visit a parse tree produced by `JobSelectionParser.start`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitStart?: (ctx: StartContext) => Result;

  /**
   * Visit a parse tree produced by `JobSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitExpr?: (ctx: ExprContext) => Result;

  /**
   * Visit a parse tree produced by `JobSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitTraversalAllowedExpr?: (ctx: TraversalAllowedExprContext) => Result;

  /**
   * Visit a parse tree produced by `JobSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAttributeExpr?: (ctx: AttributeExprContext) => Result;

  /**
   * Visit a parse tree produced by `JobSelectionParser.value`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitValue?: (ctx: ValueContext) => Result;

  /**
   * Visit a parse tree produced by `JobSelectionParser.keyValue`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitKeyValue?: (ctx: KeyValueContext) => Result;
}
