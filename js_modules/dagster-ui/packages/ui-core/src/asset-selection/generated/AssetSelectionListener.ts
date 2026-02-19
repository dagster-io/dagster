// Generated from /home/user/dagster/python_modules/dagster/dagster/_core/definitions/antlr_asset_selection/AssetSelection.g4 by ANTLR 4.13.1

import {ErrorNode, ParseTreeListener, ParserRuleContext, TerminalNode} from 'antlr4ng';

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
 * This interface defines a complete listener for a parse tree produced by
 * `AssetSelectionParser`.
 */
export class AssetSelectionListener implements ParseTreeListener {
  /**
   * Enter a parse tree produced by `AssetSelectionParser.start`.
   * @param ctx the parse tree
   */
  enterStart?: (ctx: StartContext) => void;
  /**
   * Exit a parse tree produced by `AssetSelectionParser.start`.
   * @param ctx the parse tree
   */
  exitStart?: (ctx: StartContext) => void;
  /**
   * Enter a parse tree produced by the `UpTraversalExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterUpTraversalExpression?: (ctx: UpTraversalExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `UpTraversalExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitUpTraversalExpression?: (ctx: UpTraversalExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `AndExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterAndExpression?: (ctx: AndExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `AndExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitAndExpression?: (ctx: AndExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `AllExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterAllExpression?: (ctx: AllExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `AllExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitAllExpression?: (ctx: AllExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `TraversalAllowedExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterTraversalAllowedExpression?: (ctx: TraversalAllowedExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `TraversalAllowedExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitTraversalAllowedExpression?: (ctx: TraversalAllowedExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `DownTraversalExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterDownTraversalExpression?: (ctx: DownTraversalExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `DownTraversalExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitDownTraversalExpression?: (ctx: DownTraversalExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `NotExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterNotExpression?: (ctx: NotExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `NotExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitNotExpression?: (ctx: NotExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `OrExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterOrExpression?: (ctx: OrExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `OrExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitOrExpression?: (ctx: OrExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `UpAndDownTraversalExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterUpAndDownTraversalExpression?: (ctx: UpAndDownTraversalExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `UpAndDownTraversalExpression`
   * labeled alternative in `AssetSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitUpAndDownTraversalExpression?: (ctx: UpAndDownTraversalExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `AttributeExpression`
   * labeled alternative in `AssetSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  enterAttributeExpression?: (ctx: AttributeExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `AttributeExpression`
   * labeled alternative in `AssetSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  exitAttributeExpression?: (ctx: AttributeExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `FunctionCallExpression`
   * labeled alternative in `AssetSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  enterFunctionCallExpression?: (ctx: FunctionCallExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `FunctionCallExpression`
   * labeled alternative in `AssetSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  exitFunctionCallExpression?: (ctx: FunctionCallExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `ParenthesizedExpression`
   * labeled alternative in `AssetSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  enterParenthesizedExpression?: (ctx: ParenthesizedExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `ParenthesizedExpression`
   * labeled alternative in `AssetSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  exitParenthesizedExpression?: (ctx: ParenthesizedExpressionContext) => void;
  /**
   * Enter a parse tree produced by `AssetSelectionParser.upTraversal`.
   * @param ctx the parse tree
   */
  enterUpTraversal?: (ctx: UpTraversalContext) => void;
  /**
   * Exit a parse tree produced by `AssetSelectionParser.upTraversal`.
   * @param ctx the parse tree
   */
  exitUpTraversal?: (ctx: UpTraversalContext) => void;
  /**
   * Enter a parse tree produced by `AssetSelectionParser.downTraversal`.
   * @param ctx the parse tree
   */
  enterDownTraversal?: (ctx: DownTraversalContext) => void;
  /**
   * Exit a parse tree produced by `AssetSelectionParser.downTraversal`.
   * @param ctx the parse tree
   */
  exitDownTraversal?: (ctx: DownTraversalContext) => void;
  /**
   * Enter a parse tree produced by `AssetSelectionParser.functionName`.
   * @param ctx the parse tree
   */
  enterFunctionName?: (ctx: FunctionNameContext) => void;
  /**
   * Exit a parse tree produced by `AssetSelectionParser.functionName`.
   * @param ctx the parse tree
   */
  exitFunctionName?: (ctx: FunctionNameContext) => void;
  /**
   * Enter a parse tree produced by the `KeyExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  enterKeyExpr?: (ctx: KeyExprContext) => void;
  /**
   * Exit a parse tree produced by the `KeyExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  exitKeyExpr?: (ctx: KeyExprContext) => void;
  /**
   * Enter a parse tree produced by the `TagAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  enterTagAttributeExpr?: (ctx: TagAttributeExprContext) => void;
  /**
   * Exit a parse tree produced by the `TagAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  exitTagAttributeExpr?: (ctx: TagAttributeExprContext) => void;
  /**
   * Enter a parse tree produced by the `OwnerAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  enterOwnerAttributeExpr?: (ctx: OwnerAttributeExprContext) => void;
  /**
   * Exit a parse tree produced by the `OwnerAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  exitOwnerAttributeExpr?: (ctx: OwnerAttributeExprContext) => void;
  /**
   * Enter a parse tree produced by the `GroupAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  enterGroupAttributeExpr?: (ctx: GroupAttributeExprContext) => void;
  /**
   * Exit a parse tree produced by the `GroupAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  exitGroupAttributeExpr?: (ctx: GroupAttributeExprContext) => void;
  /**
   * Enter a parse tree produced by the `KindAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  enterKindAttributeExpr?: (ctx: KindAttributeExprContext) => void;
  /**
   * Exit a parse tree produced by the `KindAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  exitKindAttributeExpr?: (ctx: KindAttributeExprContext) => void;
  /**
   * Enter a parse tree produced by the `StatusAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  enterStatusAttributeExpr?: (ctx: StatusAttributeExprContext) => void;
  /**
   * Exit a parse tree produced by the `StatusAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  exitStatusAttributeExpr?: (ctx: StatusAttributeExprContext) => void;
  /**
   * Enter a parse tree produced by the `ColumnAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  enterColumnAttributeExpr?: (ctx: ColumnAttributeExprContext) => void;
  /**
   * Exit a parse tree produced by the `ColumnAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  exitColumnAttributeExpr?: (ctx: ColumnAttributeExprContext) => void;
  /**
   * Enter a parse tree produced by the `TableNameAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  enterTableNameAttributeExpr?: (ctx: TableNameAttributeExprContext) => void;
  /**
   * Exit a parse tree produced by the `TableNameAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  exitTableNameAttributeExpr?: (ctx: TableNameAttributeExprContext) => void;
  /**
   * Enter a parse tree produced by the `ColumnTagAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  enterColumnTagAttributeExpr?: (ctx: ColumnTagAttributeExprContext) => void;
  /**
   * Exit a parse tree produced by the `ColumnTagAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  exitColumnTagAttributeExpr?: (ctx: ColumnTagAttributeExprContext) => void;
  /**
   * Enter a parse tree produced by the `CodeLocationAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  enterCodeLocationAttributeExpr?: (ctx: CodeLocationAttributeExprContext) => void;
  /**
   * Exit a parse tree produced by the `CodeLocationAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  exitCodeLocationAttributeExpr?: (ctx: CodeLocationAttributeExprContext) => void;
  /**
   * Enter a parse tree produced by the `ChangedInBranchAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  enterChangedInBranchAttributeExpr?: (ctx: ChangedInBranchAttributeExprContext) => void;
  /**
   * Exit a parse tree produced by the `ChangedInBranchAttributeExpr`
   * labeled alternative in `AssetSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  exitChangedInBranchAttributeExpr?: (ctx: ChangedInBranchAttributeExprContext) => void;
  /**
   * Enter a parse tree produced by `AssetSelectionParser.value`.
   * @param ctx the parse tree
   */
  enterValue?: (ctx: ValueContext) => void;
  /**
   * Exit a parse tree produced by `AssetSelectionParser.value`.
   * @param ctx the parse tree
   */
  exitValue?: (ctx: ValueContext) => void;
  /**
   * Enter a parse tree produced by `AssetSelectionParser.keyValue`.
   * @param ctx the parse tree
   */
  enterKeyValue?: (ctx: KeyValueContext) => void;
  /**
   * Exit a parse tree produced by `AssetSelectionParser.keyValue`.
   * @param ctx the parse tree
   */
  exitKeyValue?: (ctx: KeyValueContext) => void;

  visitTerminal(node: TerminalNode): void {}
  visitErrorNode(node: ErrorNode): void {}
  enterEveryRule(node: ParserRuleContext): void {}
  exitEveryRule(node: ParserRuleContext): void {}
}
