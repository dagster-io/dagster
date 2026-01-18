// Generated from /home/user/dagster/js_modules/dagster-ui/packages/ui-core/src/op-selection/OpSelection.g4 by ANTLR 4.13.1

import {ErrorNode, ParseTreeListener, ParserRuleContext, TerminalNode} from 'antlr4ng';

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
 * This interface defines a complete listener for a parse tree produced by
 * `OpSelectionParser`.
 */
export class OpSelectionListener implements ParseTreeListener {
  /**
   * Enter a parse tree produced by `OpSelectionParser.start`.
   * @param ctx the parse tree
   */
  enterStart?: (ctx: StartContext) => void;
  /**
   * Exit a parse tree produced by `OpSelectionParser.start`.
   * @param ctx the parse tree
   */
  exitStart?: (ctx: StartContext) => void;
  /**
   * Enter a parse tree produced by the `UpTraversalExpression`
   * labeled alternative in `OpSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterUpTraversalExpression?: (ctx: UpTraversalExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `UpTraversalExpression`
   * labeled alternative in `OpSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitUpTraversalExpression?: (ctx: UpTraversalExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `AndExpression`
   * labeled alternative in `OpSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterAndExpression?: (ctx: AndExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `AndExpression`
   * labeled alternative in `OpSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitAndExpression?: (ctx: AndExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `AllExpression`
   * labeled alternative in `OpSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterAllExpression?: (ctx: AllExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `AllExpression`
   * labeled alternative in `OpSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitAllExpression?: (ctx: AllExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `TraversalAllowedExpression`
   * labeled alternative in `OpSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterTraversalAllowedExpression?: (ctx: TraversalAllowedExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `TraversalAllowedExpression`
   * labeled alternative in `OpSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitTraversalAllowedExpression?: (ctx: TraversalAllowedExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `DownTraversalExpression`
   * labeled alternative in `OpSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterDownTraversalExpression?: (ctx: DownTraversalExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `DownTraversalExpression`
   * labeled alternative in `OpSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitDownTraversalExpression?: (ctx: DownTraversalExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `NotExpression`
   * labeled alternative in `OpSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterNotExpression?: (ctx: NotExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `NotExpression`
   * labeled alternative in `OpSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitNotExpression?: (ctx: NotExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `OrExpression`
   * labeled alternative in `OpSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterOrExpression?: (ctx: OrExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `OrExpression`
   * labeled alternative in `OpSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitOrExpression?: (ctx: OrExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `UpAndDownTraversalExpression`
   * labeled alternative in `OpSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterUpAndDownTraversalExpression?: (ctx: UpAndDownTraversalExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `UpAndDownTraversalExpression`
   * labeled alternative in `OpSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitUpAndDownTraversalExpression?: (ctx: UpAndDownTraversalExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `AttributeExpression`
   * labeled alternative in `OpSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  enterAttributeExpression?: (ctx: AttributeExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `AttributeExpression`
   * labeled alternative in `OpSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  exitAttributeExpression?: (ctx: AttributeExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `FunctionCallExpression`
   * labeled alternative in `OpSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  enterFunctionCallExpression?: (ctx: FunctionCallExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `FunctionCallExpression`
   * labeled alternative in `OpSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  exitFunctionCallExpression?: (ctx: FunctionCallExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `ParenthesizedExpression`
   * labeled alternative in `OpSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  enterParenthesizedExpression?: (ctx: ParenthesizedExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `ParenthesizedExpression`
   * labeled alternative in `OpSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  exitParenthesizedExpression?: (ctx: ParenthesizedExpressionContext) => void;
  /**
   * Enter a parse tree produced by `OpSelectionParser.upTraversal`.
   * @param ctx the parse tree
   */
  enterUpTraversal?: (ctx: UpTraversalContext) => void;
  /**
   * Exit a parse tree produced by `OpSelectionParser.upTraversal`.
   * @param ctx the parse tree
   */
  exitUpTraversal?: (ctx: UpTraversalContext) => void;
  /**
   * Enter a parse tree produced by `OpSelectionParser.downTraversal`.
   * @param ctx the parse tree
   */
  enterDownTraversal?: (ctx: DownTraversalContext) => void;
  /**
   * Exit a parse tree produced by `OpSelectionParser.downTraversal`.
   * @param ctx the parse tree
   */
  exitDownTraversal?: (ctx: DownTraversalContext) => void;
  /**
   * Enter a parse tree produced by `OpSelectionParser.functionName`.
   * @param ctx the parse tree
   */
  enterFunctionName?: (ctx: FunctionNameContext) => void;
  /**
   * Exit a parse tree produced by `OpSelectionParser.functionName`.
   * @param ctx the parse tree
   */
  exitFunctionName?: (ctx: FunctionNameContext) => void;
  /**
   * Enter a parse tree produced by the `NameExpr`
   * labeled alternative in `OpSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  enterNameExpr?: (ctx: NameExprContext) => void;
  /**
   * Exit a parse tree produced by the `NameExpr`
   * labeled alternative in `OpSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  exitNameExpr?: (ctx: NameExprContext) => void;
  /**
   * Enter a parse tree produced by `OpSelectionParser.value`.
   * @param ctx the parse tree
   */
  enterValue?: (ctx: ValueContext) => void;
  /**
   * Exit a parse tree produced by `OpSelectionParser.value`.
   * @param ctx the parse tree
   */
  exitValue?: (ctx: ValueContext) => void;
  /**
   * Enter a parse tree produced by `OpSelectionParser.keyValue`.
   * @param ctx the parse tree
   */
  enterKeyValue?: (ctx: KeyValueContext) => void;
  /**
   * Exit a parse tree produced by `OpSelectionParser.keyValue`.
   * @param ctx the parse tree
   */
  exitKeyValue?: (ctx: KeyValueContext) => void;

  visitTerminal(node: TerminalNode): void {}
  visitErrorNode(node: ErrorNode): void {}
  enterEveryRule(node: ParserRuleContext): void {}
  exitEveryRule(node: ParserRuleContext): void {}
}
