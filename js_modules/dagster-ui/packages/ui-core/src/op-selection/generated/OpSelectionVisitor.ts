// Generated from /home/user/dagster/js_modules/dagster-ui/packages/ui-core/src/op-selection/OpSelection.g4 by ANTLR 4.13.1

import {AbstractParseTreeVisitor} from 'antlr4ng';

import {StartContext} from './OpSelectionParser.js';
import {UpTraversalExpressionContext} from './OpSelectionParser.js';
import {AndExpressionContext} from './OpSelectionParser.js';
import {AllExpressionContext} from './OpSelectionParser.js';
import {TraversalAllowedExpressionContext} from './OpSelectionParser.js';
import {DownTraversalExpressionContext} from './OpSelectionParser.js';
import {NotExpressionContext} from './OpSelectionParser.js';
import {OrExpressionContext} from './OpSelectionParser.js';
import {UpAndDownTraversalExpressionContext} from './OpSelectionParser.js';
import {AttributeExpressionContext} from './OpSelectionParser.js';
import {FunctionCallExpressionContext} from './OpSelectionParser.js';
import {ParenthesizedExpressionContext} from './OpSelectionParser.js';
import {UpTraversalContext} from './OpSelectionParser.js';
import {DownTraversalContext} from './OpSelectionParser.js';
import {FunctionNameContext} from './OpSelectionParser.js';
import {NameExprContext} from './OpSelectionParser.js';
import {ValueContext} from './OpSelectionParser.js';
import {KeyValueContext} from './OpSelectionParser.js';

/**
 * This interface defines a complete generic visitor for a parse tree produced
 * by `OpSelectionParser`.
 *
 * @param <Result> The return type of the visit operation. Use `void` for
 * operations with no return type.
 */
export class OpSelectionVisitor<Result> extends AbstractParseTreeVisitor<Result> {
  /**
   * Visit a parse tree produced by `OpSelectionParser.start`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitStart?: (ctx: StartContext) => Result;
  /**
   * Visit a parse tree produced by the `UpTraversalExpression`
   * labeled alternative in `OpSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUpTraversalExpression?: (ctx: UpTraversalExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `AndExpression`
   * labeled alternative in `OpSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAndExpression?: (ctx: AndExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `AllExpression`
   * labeled alternative in `OpSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAllExpression?: (ctx: AllExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `TraversalAllowedExpression`
   * labeled alternative in `OpSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitTraversalAllowedExpression?: (ctx: TraversalAllowedExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `DownTraversalExpression`
   * labeled alternative in `OpSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitDownTraversalExpression?: (ctx: DownTraversalExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `NotExpression`
   * labeled alternative in `OpSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitNotExpression?: (ctx: NotExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `OrExpression`
   * labeled alternative in `OpSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitOrExpression?: (ctx: OrExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `UpAndDownTraversalExpression`
   * labeled alternative in `OpSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUpAndDownTraversalExpression?: (ctx: UpAndDownTraversalExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `AttributeExpression`
   * labeled alternative in `OpSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAttributeExpression?: (ctx: AttributeExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `FunctionCallExpression`
   * labeled alternative in `OpSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitFunctionCallExpression?: (ctx: FunctionCallExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `ParenthesizedExpression`
   * labeled alternative in `OpSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitParenthesizedExpression?: (ctx: ParenthesizedExpressionContext) => Result;
  /**
   * Visit a parse tree produced by `OpSelectionParser.upTraversal`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUpTraversal?: (ctx: UpTraversalContext) => Result;
  /**
   * Visit a parse tree produced by `OpSelectionParser.downTraversal`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitDownTraversal?: (ctx: DownTraversalContext) => Result;
  /**
   * Visit a parse tree produced by `OpSelectionParser.functionName`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitFunctionName?: (ctx: FunctionNameContext) => Result;
  /**
   * Visit a parse tree produced by the `NameExpr`
   * labeled alternative in `OpSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitNameExpr?: (ctx: NameExprContext) => Result;
  /**
   * Visit a parse tree produced by `OpSelectionParser.value`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitValue?: (ctx: ValueContext) => Result;
  /**
   * Visit a parse tree produced by `OpSelectionParser.keyValue`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitKeyValue?: (ctx: KeyValueContext) => Result;
}
