// Generated from /home/user/dagster/js_modules/dagster-ui/packages/ui-core/src/job-selection/JobSelection.g4 by ANTLR 4.13.1

import {AbstractParseTreeVisitor} from 'antlr4ng';

import {StartContext} from './JobSelectionParser.js';
import {AndExpressionContext} from './JobSelectionParser.js';
import {AllExpressionContext} from './JobSelectionParser.js';
import {TraversalAllowedExpressionContext} from './JobSelectionParser.js';
import {NotExpressionContext} from './JobSelectionParser.js';
import {OrExpressionContext} from './JobSelectionParser.js';
import {AttributeExpressionContext} from './JobSelectionParser.js';
import {ParenthesizedExpressionContext} from './JobSelectionParser.js';
import {NameExprContext} from './JobSelectionParser.js';
import {CodeLocationExprContext} from './JobSelectionParser.js';
import {ValueContext} from './JobSelectionParser.js';
import {KeyValueContext} from './JobSelectionParser.js';

/**
 * This interface defines a complete generic visitor for a parse tree produced
 * by `JobSelectionParser`.
 *
 * @param <Result> The return type of the visit operation. Use `void` for
 * operations with no return type.
 */
export class JobSelectionVisitor<Result> extends AbstractParseTreeVisitor<Result> {
  /**
   * Visit a parse tree produced by `JobSelectionParser.start`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitStart?: (ctx: StartContext) => Result;
  /**
   * Visit a parse tree produced by the `AndExpression`
   * labeled alternative in `JobSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAndExpression?: (ctx: AndExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `AllExpression`
   * labeled alternative in `JobSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAllExpression?: (ctx: AllExpressionContext) => Result;
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
   * Visit a parse tree produced by the `OrExpression`
   * labeled alternative in `JobSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitOrExpression?: (ctx: OrExpressionContext) => Result;
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
