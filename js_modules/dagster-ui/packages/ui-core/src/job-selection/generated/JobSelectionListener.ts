// Generated from /home/user/dagster/js_modules/dagster-ui/packages/ui-core/src/job-selection/JobSelection.g4 by ANTLR 4.13.1

import {ErrorNode, ParseTreeListener, ParserRuleContext, TerminalNode} from 'antlr4ng';

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
 * This interface defines a complete listener for a parse tree produced by
 * `JobSelectionParser`.
 */
export class JobSelectionListener implements ParseTreeListener {
  /**
   * Enter a parse tree produced by `JobSelectionParser.start`.
   * @param ctx the parse tree
   */
  enterStart?: (ctx: StartContext) => void;
  /**
   * Exit a parse tree produced by `JobSelectionParser.start`.
   * @param ctx the parse tree
   */
  exitStart?: (ctx: StartContext) => void;
  /**
   * Enter a parse tree produced by the `AndExpression`
   * labeled alternative in `JobSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterAndExpression?: (ctx: AndExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `AndExpression`
   * labeled alternative in `JobSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitAndExpression?: (ctx: AndExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `AllExpression`
   * labeled alternative in `JobSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterAllExpression?: (ctx: AllExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `AllExpression`
   * labeled alternative in `JobSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitAllExpression?: (ctx: AllExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `TraversalAllowedExpression`
   * labeled alternative in `JobSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterTraversalAllowedExpression?: (ctx: TraversalAllowedExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `TraversalAllowedExpression`
   * labeled alternative in `JobSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitTraversalAllowedExpression?: (ctx: TraversalAllowedExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `NotExpression`
   * labeled alternative in `JobSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterNotExpression?: (ctx: NotExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `NotExpression`
   * labeled alternative in `JobSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitNotExpression?: (ctx: NotExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `OrExpression`
   * labeled alternative in `JobSelectionParser.expr`.
   * @param ctx the parse tree
   */
  enterOrExpression?: (ctx: OrExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `OrExpression`
   * labeled alternative in `JobSelectionParser.expr`.
   * @param ctx the parse tree
   */
  exitOrExpression?: (ctx: OrExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `AttributeExpression`
   * labeled alternative in `JobSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  enterAttributeExpression?: (ctx: AttributeExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `AttributeExpression`
   * labeled alternative in `JobSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  exitAttributeExpression?: (ctx: AttributeExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `ParenthesizedExpression`
   * labeled alternative in `JobSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  enterParenthesizedExpression?: (ctx: ParenthesizedExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `ParenthesizedExpression`
   * labeled alternative in `JobSelectionParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  exitParenthesizedExpression?: (ctx: ParenthesizedExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `NameExpr`
   * labeled alternative in `JobSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  enterNameExpr?: (ctx: NameExprContext) => void;
  /**
   * Exit a parse tree produced by the `NameExpr`
   * labeled alternative in `JobSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  exitNameExpr?: (ctx: NameExprContext) => void;
  /**
   * Enter a parse tree produced by the `CodeLocationExpr`
   * labeled alternative in `JobSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  enterCodeLocationExpr?: (ctx: CodeLocationExprContext) => void;
  /**
   * Exit a parse tree produced by the `CodeLocationExpr`
   * labeled alternative in `JobSelectionParser.attributeExpr`.
   * @param ctx the parse tree
   */
  exitCodeLocationExpr?: (ctx: CodeLocationExprContext) => void;
  /**
   * Enter a parse tree produced by `JobSelectionParser.value`.
   * @param ctx the parse tree
   */
  enterValue?: (ctx: ValueContext) => void;
  /**
   * Exit a parse tree produced by `JobSelectionParser.value`.
   * @param ctx the parse tree
   */
  exitValue?: (ctx: ValueContext) => void;
  /**
   * Enter a parse tree produced by `JobSelectionParser.keyValue`.
   * @param ctx the parse tree
   */
  enterKeyValue?: (ctx: KeyValueContext) => void;
  /**
   * Exit a parse tree produced by `JobSelectionParser.keyValue`.
   * @param ctx the parse tree
   */
  exitKeyValue?: (ctx: KeyValueContext) => void;

  visitTerminal(node: TerminalNode): void {}
  visitErrorNode(node: ErrorNode): void {}
  enterEveryRule(node: ParserRuleContext): void {}
  exitEveryRule(node: ParserRuleContext): void {}
}
