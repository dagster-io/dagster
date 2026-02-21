// Generated from /home/user/dagster/python_modules/dagster/dagster/_core/definitions/antlr_asset_selection/AssetSelection.g4 by ANTLR 4.13.1

import {AbstractParseTreeVisitor} from 'antlr4ng';

import {StartContext} from './AssetSelectionParser.js';
import {UpTraversalExpressionContext} from './AssetSelectionParser.js';
import {AndExpressionContext} from './AssetSelectionParser.js';
import {AllExpressionContext} from './AssetSelectionParser.js';
import {TraversalAllowedExpressionContext} from './AssetSelectionParser.js';
import {DownTraversalExpressionContext} from './AssetSelectionParser.js';
import {NotExpressionContext} from './AssetSelectionParser.js';
import {OrExpressionContext} from './AssetSelectionParser.js';
import {UpAndDownTraversalExpressionContext} from './AssetSelectionParser.js';
import {AttributeExpressionContext} from './AssetSelectionParser.js';
import {FunctionCallExpressionContext} from './AssetSelectionParser.js';
import {ParenthesizedExpressionContext} from './AssetSelectionParser.js';
import {UpTraversalContext} from './AssetSelectionParser.js';
import {DownTraversalContext} from './AssetSelectionParser.js';
import {FunctionNameContext} from './AssetSelectionParser.js';
import {KeyExprContext} from './AssetSelectionParser.js';
import {TagAttributeExprContext} from './AssetSelectionParser.js';
import {OwnerAttributeExprContext} from './AssetSelectionParser.js';
import {GroupAttributeExprContext} from './AssetSelectionParser.js';
import {KindAttributeExprContext} from './AssetSelectionParser.js';
import {StatusAttributeExprContext} from './AssetSelectionParser.js';
import {ColumnAttributeExprContext} from './AssetSelectionParser.js';
import {TableNameAttributeExprContext} from './AssetSelectionParser.js';
import {ColumnTagAttributeExprContext} from './AssetSelectionParser.js';
import {CodeLocationAttributeExprContext} from './AssetSelectionParser.js';
import {ChangedInBranchAttributeExprContext} from './AssetSelectionParser.js';
import {ValueContext} from './AssetSelectionParser.js';
import {KeyValueContext} from './AssetSelectionParser.js';

/**
 * This interface defines a complete generic visitor for a parse tree produced
 * by `AssetSelectionParser`.
 *
 * @param <Result> The return type of the visit operation. Use `void` for
 * operations with no return type.
 */
export class AssetSelectionVisitor<Result> extends AbstractParseTreeVisitor<Result> {
  /**
   * Visit a parse tree produced by `AssetSelectionParser.start`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitStart?: (ctx: StartContext) => Result;
  /**
   * Visit a parse tree produced by the `UpTraversalExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUpTraversalExpression?: (ctx: UpTraversalExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `AndExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAndExpression?: (ctx: AndExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `AllExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAllExpression?: (ctx: AllExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `TraversalAllowedExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitTraversalAllowedExpression?: (ctx: TraversalAllowedExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `DownTraversalExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitDownTraversalExpression?: (ctx: DownTraversalExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `NotExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitNotExpression?: (ctx: NotExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `OrExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitOrExpression?: (ctx: OrExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `UpAndDownTraversalExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUpAndDownTraversalExpression?: (ctx: UpAndDownTraversalExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `AttributeExpression`
   * labeled alternative in `AssetSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAttributeExpression?: (ctx: AttributeExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `FunctionCallExpression`
   * labeled alternative in `AssetSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitFunctionCallExpression?: (ctx: FunctionCallExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `ParenthesizedExpression`
   * labeled alternative in `AssetSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitParenthesizedExpression?: (ctx: ParenthesizedExpressionContext) => Result;
  /**
   * Visit a parse tree produced by `AssetSelectionParser.upTraversal`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUpTraversal?: (ctx: UpTraversalContext) => Result;
  /**
   * Visit a parse tree produced by `AssetSelectionParser.downTraversal`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitDownTraversal?: (ctx: DownTraversalContext) => Result;
  /**
   * Visit a parse tree produced by `AssetSelectionParser.functionName`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitFunctionName?: (ctx: FunctionNameContext) => Result;
  /**
   * Visit a parse tree produced by the `KeyExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitKeyExpr?: (ctx: KeyExprContext) => Result;
  /**
   * Visit a parse tree produced by the `TagAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitTagAttributeExpr?: (ctx: TagAttributeExprContext) => Result;
  /**
   * Visit a parse tree produced by the `OwnerAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitOwnerAttributeExpr?: (ctx: OwnerAttributeExprContext) => Result;
  /**
   * Visit a parse tree produced by the `GroupAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitGroupAttributeExpr?: (ctx: GroupAttributeExprContext) => Result;
  /**
   * Visit a parse tree produced by the `KindAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitKindAttributeExpr?: (ctx: KindAttributeExprContext) => Result;
  /**
   * Visit a parse tree produced by the `StatusAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitStatusAttributeExpr?: (ctx: StatusAttributeExprContext) => Result;
  /**
   * Visit a parse tree produced by the `ColumnAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitColumnAttributeExpr?: (ctx: ColumnAttributeExprContext) => Result;
  /**
   * Visit a parse tree produced by the `TableNameAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitTableNameAttributeExpr?: (ctx: TableNameAttributeExprContext) => Result;
  /**
   * Visit a parse tree produced by the `ColumnTagAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitColumnTagAttributeExpr?: (ctx: ColumnTagAttributeExprContext) => Result;
  /**
   * Visit a parse tree produced by the `CodeLocationAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitCodeLocationAttributeExpr?: (ctx: CodeLocationAttributeExprContext) => Result;
  /**
   * Visit a parse tree produced by the `ChangedInBranchAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitChangedInBranchAttributeExpr?: (ctx: ChangedInBranchAttributeExprContext) => Result;
  /**
   * Visit a parse tree produced by `AssetSelectionParser.value`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitValue?: (ctx: ValueContext) => Result;
  /**
   * Visit a parse tree produced by `AssetSelectionParser.keyValue`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitKeyValue?: (ctx: KeyValueContext) => Result;
}
