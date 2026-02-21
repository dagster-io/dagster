// Generated from /home/user/dagster/js_modules/dagster-ui/packages/ui-core/src/run-selection/RunSelection.g4 by ANTLR 4.13.1

import {AbstractParseTreeVisitor} from 'antlr4ng';

import {StartContext} from './RunSelectionParser.js';
import {UpTraversalExpressionContext} from './RunSelectionParser.js';
import {AndExpressionContext} from './RunSelectionParser.js';
import {AllExpressionContext} from './RunSelectionParser.js';
import {TraversalAllowedExpressionContext} from './RunSelectionParser.js';
import {DownTraversalExpressionContext} from './RunSelectionParser.js';
import {NotExpressionContext} from './RunSelectionParser.js';
import {OrExpressionContext} from './RunSelectionParser.js';
import {UpAndDownTraversalExpressionContext} from './RunSelectionParser.js';
import {AttributeExpressionContext} from './RunSelectionParser.js';
import {FunctionCallExpressionContext} from './RunSelectionParser.js';
import {ParenthesizedExpressionContext} from './RunSelectionParser.js';
import {UpTraversalContext} from './RunSelectionParser.js';
import {DownTraversalContext} from './RunSelectionParser.js';
import {FunctionNameContext} from './RunSelectionParser.js';
import {NameExprContext} from './RunSelectionParser.js';
import {StatusAttributeExprContext} from './RunSelectionParser.js';
import {ValueContext} from './RunSelectionParser.js';
import {KeyValueContext} from './RunSelectionParser.js';

/**
 * This interface defines a complete generic visitor for a parse tree produced
 * by `RunSelectionParser`.
 *
 * @param <Result> The return type of the visit operation. Use `void` for
 * operations with no return type.
 */
export class RunSelectionVisitor<Result> extends AbstractParseTreeVisitor<Result> {
  /**
   * Visit a parse tree produced by `RunSelectionParser.start`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitStart?: (ctx: StartContext) => Result;
  /**
   * Visit a parse tree produced by the `UpTraversalExpression`
   * labeled alternative in `RunSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUpTraversalExpression?: (ctx: UpTraversalExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `AndExpression`
   * labeled alternative in `RunSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAndExpression?: (ctx: AndExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `AllExpression`
   * labeled alternative in `RunSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAllExpression?: (ctx: AllExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `TraversalAllowedExpression`
   * labeled alternative in `RunSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitTraversalAllowedExpression?: (ctx: TraversalAllowedExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `DownTraversalExpression`
   * labeled alternative in `RunSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitDownTraversalExpression?: (ctx: DownTraversalExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `NotExpression`
   * labeled alternative in `RunSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitNotExpression?: (ctx: NotExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `OrExpression`
   * labeled alternative in `RunSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitOrExpression?: (ctx: OrExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `UpAndDownTraversalExpression`
   * labeled alternative in `RunSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUpAndDownTraversalExpression?: (ctx: UpAndDownTraversalExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `AttributeExpression`
   * labeled alternative in `RunSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAttributeExpression?: (ctx: AttributeExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `FunctionCallExpression`
   * labeled alternative in `RunSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitFunctionCallExpression?: (ctx: FunctionCallExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `ParenthesizedExpression`
   * labeled alternative in `RunSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitParenthesizedExpression?: (ctx: ParenthesizedExpressionContext) => Result;
  /**
   * Visit a parse tree produced by `RunSelectionParser.upTraversal`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUpTraversal?: (ctx: UpTraversalContext) => Result;
  /**
   * Visit a parse tree produced by `RunSelectionParser.downTraversal`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitDownTraversal?: (ctx: DownTraversalContext) => Result;
  /**
   * Visit a parse tree produced by `RunSelectionParser.functionName`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitFunctionName?: (ctx: FunctionNameContext) => Result;
  /**
   * Visit a parse tree produced by the `NameExpr`
   * labeled alternative in `RunSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitNameExpr?: (ctx: NameExprContext) => Result;
  /**
   * Visit a parse tree produced by the `StatusAttributeExpr`
   * labeled alternative in `RunSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitStatusAttributeExpr?: (ctx: StatusAttributeExprContext) => Result;
  /**
   * Visit a parse tree produced by `RunSelectionParser.value`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitValue?: (ctx: ValueContext) => Result;
  /**
   * Visit a parse tree produced by `RunSelectionParser.keyValue`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitKeyValue?: (ctx: KeyValueContext) => Result;
}
