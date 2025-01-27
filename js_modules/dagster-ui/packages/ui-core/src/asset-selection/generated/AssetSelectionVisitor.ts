// Generated from /Users/marcosalazar/code/dagster/python_modules/dagster/dagster/_core/definitions/antlr_asset_selection/AssetSelection.g4 by ANTLR 4.9.0-SNAPSHOT

import {ParseTreeVisitor} from 'antlr4ts/tree/ParseTreeVisitor';

import {
  AllExpressionContext,
  AndExpressionContext,
  AttributeExprContext,
  AttributeExpressionContext,
  CodeLocationAttributeExprContext,
  DownTraversalContext,
  DownTraversalExpressionContext,
  ExprContext,
  FunctionCallExpressionContext,
  FunctionNameContext,
  GroupAttributeExprContext,
  KeyExprContext,
  KeySubstringExprContext,
  KindAttributeExprContext,
  NotExpressionContext,
  OrExpressionContext,
  OwnerAttributeExprContext,
  ParenthesizedExpressionContext,
  StartContext,
  TagAttributeExprContext,
  TraversalAllowedExprContext,
  TraversalAllowedExpressionContext,
  UpAndDownTraversalExpressionContext,
  UpTraversalContext,
  UpTraversalExpressionContext,
  ValueContext,
} from './AssetSelectionParser';

/**
 * This interface defines a complete generic visitor for a parse tree produced
 * by `AssetSelectionParser`.
 *
 * @param <Result> The return type of the visit operation. Use `void` for
 * operations with no return type.
 */
export interface AssetSelectionVisitor<Result> extends ParseTreeVisitor<Result> {
  /**
   * Visit a parse tree produced by the `TraversalAllowedExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitTraversalAllowedExpression?: (ctx: TraversalAllowedExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `UpAndDownTraversalExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUpAndDownTraversalExpression?: (ctx: UpAndDownTraversalExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `UpTraversalExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUpTraversalExpression?: (ctx: UpTraversalExpressionContext) => Result;

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
   * Visit a parse tree produced by the `AndExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAndExpression?: (ctx: AndExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `OrExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitOrExpression?: (ctx: OrExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `AllExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAllExpression?: (ctx: AllExpressionContext) => Result;

  /**
   * Visit a parse tree produced by the `KeyExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitKeyExpr?: (ctx: KeyExprContext) => Result;

  /**
   * Visit a parse tree produced by the `KeySubstringExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitKeySubstringExpr?: (ctx: KeySubstringExprContext) => Result;

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
   * Visit a parse tree produced by the `CodeLocationAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitCodeLocationAttributeExpr?: (ctx: CodeLocationAttributeExprContext) => Result;

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
   * Visit a parse tree produced by `AssetSelectionParser.start`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitStart?: (ctx: StartContext) => Result;

  /**
   * Visit a parse tree produced by `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitExpr?: (ctx: ExprContext) => Result;

  /**
   * Visit a parse tree produced by `AssetSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitTraversalAllowedExpr?: (ctx: TraversalAllowedExprContext) => Result;

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
   * Visit a parse tree produced by `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAttributeExpr?: (ctx: AttributeExprContext) => Result;

  /**
   * Visit a parse tree produced by `AssetSelectionParser.value`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitValue?: (ctx: ValueContext) => Result;
}
