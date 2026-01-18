// Generated from /home/user/dagster/js_modules/dagster-ui/packages/ui-core/src/run-selection/RunSelection.g4 by ANTLR 4.13.1

import {ErrorNode, ParseTreeListener, ParserRuleContext, TerminalNode} from 'antlr4ng';

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
 * This interface defines a complete listener for a parse tree produced by
 * `RunSelectionParser`.
 */
export class RunSelectionListener implements ParseTreeListener {
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
   * Enter a parse tree produced by `RunSelectionParser.value`.
   * @param ctx the parse tree
   */
  enterValue?: (ctx: ValueContext) => void;
  /**
   * Exit a parse tree produced by `RunSelectionParser.value`.
   * @param ctx the parse tree
   */
  exitValue?: (ctx: ValueContext) => void;
  /**
   * Enter a parse tree produced by `RunSelectionParser.keyValue`.
   * @param ctx the parse tree
   */
  enterKeyValue?: (ctx: KeyValueContext) => void;
  /**
   * Exit a parse tree produced by `RunSelectionParser.keyValue`.
   * @param ctx the parse tree
   */
  exitKeyValue?: (ctx: KeyValueContext) => void;

  visitTerminal(node: TerminalNode): void {}
  visitErrorNode(node: ErrorNode): void {}
  enterEveryRule(node: ParserRuleContext): void {}
  exitEveryRule(node: ParserRuleContext): void {}
}
