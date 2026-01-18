// Generated from /home/user/dagster/js_modules/dagster-ui/packages/ui-core/src/automation-selection/AutomationSelection.g4 by ANTLR 4.13.1

import {AbstractParseTreeVisitor} from 'antlr4ng';

import {StartContext} from './AutomationSelectionParser.js';
import {AndExpressionContext} from './AutomationSelectionParser.js';
import {AllExpressionContext} from './AutomationSelectionParser.js';
import {TraversalAllowedExpressionContext} from './AutomationSelectionParser.js';
import {NotExpressionContext} from './AutomationSelectionParser.js';
import {OrExpressionContext} from './AutomationSelectionParser.js';
import {AttributeExpressionContext} from './AutomationSelectionParser.js';
import {ParenthesizedExpressionContext} from './AutomationSelectionParser.js';
import {NameExprContext} from './AutomationSelectionParser.js';
import {TagExprContext} from './AutomationSelectionParser.js';
import {TypeExprContext} from './AutomationSelectionParser.js';
import {StatusExprContext} from './AutomationSelectionParser.js';
import {CodeLocationExprContext} from './AutomationSelectionParser.js';
import {ValueContext} from './AutomationSelectionParser.js';
import {KeyValueContext} from './AutomationSelectionParser.js';

/**
 * This interface defines a complete generic visitor for a parse tree produced
 * by `AutomationSelectionParser`.
 *
 * @param <Result> The return type of the visit operation. Use `void` for
 * operations with no return type.
 */
export class AutomationSelectionVisitor<Result> extends AbstractParseTreeVisitor<Result> {
  /**
   * Visit a parse tree produced by `AutomationSelectionParser.start`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitStart?: (ctx: StartContext) => Result;
  /**
   * Visit a parse tree produced by the `AndExpression`
   * labeled alternative in `AutomationSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAndExpression?: (ctx: AndExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `AllExpression`
   * labeled alternative in `AutomationSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAllExpression?: (ctx: AllExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `TraversalAllowedExpression`
   * labeled alternative in `AutomationSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitTraversalAllowedExpression?: (ctx: TraversalAllowedExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `NotExpression`
   * labeled alternative in `AutomationSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitNotExpression?: (ctx: NotExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `OrExpression`
   * labeled alternative in `AutomationSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitOrExpression?: (ctx: OrExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `AttributeExpression`
   * labeled alternative in `AutomationSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAttributeExpression?: (ctx: AttributeExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `ParenthesizedExpression`
   * labeled alternative in `AutomationSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitParenthesizedExpression?: (ctx: ParenthesizedExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `NameExpr`
   * labeled alternative in `AutomationSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitNameExpr?: (ctx: NameExprContext) => Result;
  /**
   * Visit a parse tree produced by the `TagExpr`
   * labeled alternative in `AutomationSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitTagExpr?: (ctx: TagExprContext) => Result;
  /**
   * Visit a parse tree produced by the `TypeExpr`
   * labeled alternative in `AutomationSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitTypeExpr?: (ctx: TypeExprContext) => Result;
  /**
   * Visit a parse tree produced by the `StatusExpr`
   * labeled alternative in `AutomationSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitStatusExpr?: (ctx: StatusExprContext) => Result;
  /**
   * Visit a parse tree produced by the `CodeLocationExpr`
   * labeled alternative in `AutomationSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitCodeLocationExpr?: (ctx: CodeLocationExprContext) => Result;
  /**
   * Visit a parse tree produced by `AutomationSelectionParser.value`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitValue?: (ctx: ValueContext) => Result;
  /**
   * Visit a parse tree produced by `AutomationSelectionParser.keyValue`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitKeyValue?: (ctx: KeyValueContext) => Result;
}
