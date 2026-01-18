// Generated from /home/user/dagster/js_modules/dagster-ui/packages/ui-core/src/selection/SelectionAutoComplete.g4 by ANTLR 4.13.1

import {ErrorNode, ParseTreeListener, ParserRuleContext, TerminalNode} from 'antlr4ng';

import {StartContext} from './SelectionAutoCompleteParser.js';
import {CommaExpressionWrapper3Context} from './SelectionAutoCompleteParser.js';
import {UpTraversalExpressionContext} from './SelectionAutoCompleteParser.js';
import {CommaExpressionWrapper2Context} from './SelectionAutoCompleteParser.js';
import {CommaExpressionWrapper1Context} from './SelectionAutoCompleteParser.js';
import {AllExpressionContext} from './SelectionAutoCompleteParser.js';
import {NotExpressionContext} from './SelectionAutoCompleteParser.js';
import {OrExpressionContext} from './SelectionAutoCompleteParser.js';
import {UpAndDownTraversalExpressionContext} from './SelectionAutoCompleteParser.js';
import {UnmatchedValueContext} from './SelectionAutoCompleteParser.js';
import {AndExpressionContext} from './SelectionAutoCompleteParser.js';
import {TraversalAllowedExpressionContext} from './SelectionAutoCompleteParser.js';
import {DownTraversalExpressionContext} from './SelectionAutoCompleteParser.js';
import {IncompleteOrExpressionContext} from './SelectionAutoCompleteParser.js';
import {IncompleteNotExpressionContext} from './SelectionAutoCompleteParser.js';
import {IncompleteAndExpressionContext} from './SelectionAutoCompleteParser.js';
import {AttributeExpressionContext} from './SelectionAutoCompleteParser.js';
import {FunctionCallExpressionContext} from './SelectionAutoCompleteParser.js';
import {TraversalAllowedParenthesizedExpressionContext} from './SelectionAutoCompleteParser.js';
import {IncompleteExpressionContext} from './SelectionAutoCompleteParser.js';
import {ParenthesizedExpressionContext} from './SelectionAutoCompleteParser.js';
import {IncompleteAttributeExpressionMissingSecondValueContext} from './SelectionAutoCompleteParser.js';
import {IncompleteAttributeExpressionMissingValueContext} from './SelectionAutoCompleteParser.js';
import {ExpressionlessFunctionExpressionContext} from './SelectionAutoCompleteParser.js';
import {UnclosedExpressionlessFunctionExpressionContext} from './SelectionAutoCompleteParser.js';
import {UnclosedFunctionExpressionContext} from './SelectionAutoCompleteParser.js';
import {UnclosedParenthesizedExpressionContext} from './SelectionAutoCompleteParser.js';
import {ExpressionlessParenthesizedExpressionWrapperContext} from './SelectionAutoCompleteParser.js';
import {UnclosedExpressionlessParenthesizedExpressionContext} from './SelectionAutoCompleteParser.js';
import {IncompletePlusTraversalExpressionContext} from './SelectionAutoCompleteParser.js';
import {IncompletePlusTraversalExpressionMissingValueContext} from './SelectionAutoCompleteParser.js';
import {IncompleteAttributeExpressionMissingKeyContext} from './SelectionAutoCompleteParser.js';
import {ExpressionlessParenthesizedExpressionContext} from './SelectionAutoCompleteParser.js';
import {UpTraversalContext} from './SelectionAutoCompleteParser.js';
import {DownTraversalContext} from './SelectionAutoCompleteParser.js';
import {UpTraversalTokenContext} from './SelectionAutoCompleteParser.js';
import {DownTraversalTokenContext} from './SelectionAutoCompleteParser.js';
import {AttributeNameContext} from './SelectionAutoCompleteParser.js';
import {AttributeValueContext} from './SelectionAutoCompleteParser.js';
import {FunctionNameContext} from './SelectionAutoCompleteParser.js';
import {CommaTokenContext} from './SelectionAutoCompleteParser.js';
import {OrTokenContext} from './SelectionAutoCompleteParser.js';
import {AndTokenContext} from './SelectionAutoCompleteParser.js';
import {NotTokenContext} from './SelectionAutoCompleteParser.js';
import {ColonTokenContext} from './SelectionAutoCompleteParser.js';
import {LeftParenTokenContext} from './SelectionAutoCompleteParser.js';
import {RightParenTokenContext} from './SelectionAutoCompleteParser.js';
import {AttributeValueWhitespaceContext} from './SelectionAutoCompleteParser.js';
import {PostAttributeValueWhitespaceContext} from './SelectionAutoCompleteParser.js';
import {PostExpressionWhitespaceContext} from './SelectionAutoCompleteParser.js';
import {PostNotOperatorWhitespaceContext} from './SelectionAutoCompleteParser.js';
import {PostLogicalOperatorWhitespaceContext} from './SelectionAutoCompleteParser.js';
import {PostNeighborTraversalWhitespaceContext} from './SelectionAutoCompleteParser.js';
import {PostUpwardTraversalWhitespaceContext} from './SelectionAutoCompleteParser.js';
import {PostDownwardTraversalWhitespaceContext} from './SelectionAutoCompleteParser.js';
import {PostDigitsWhitespaceContext} from './SelectionAutoCompleteParser.js';
import {QuotedStringValueContext} from './SelectionAutoCompleteParser.js';
import {IncompleteLeftQuotedStringValueContext} from './SelectionAutoCompleteParser.js';
import {IncompleteRightQuotedStringValueContext} from './SelectionAutoCompleteParser.js';
import {UnquotedStringValueContext} from './SelectionAutoCompleteParser.js';
import {NullStringValueContext} from './SelectionAutoCompleteParser.js';
import {DigitsValueContext} from './SelectionAutoCompleteParser.js';

/**
 * This interface defines a complete listener for a parse tree produced by
 * `SelectionAutoCompleteParser`.
 */
export class SelectionAutoCompleteListener implements ParseTreeListener {
  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.start`.
   * @param ctx the parse tree
   */
  enterStart?: (ctx: StartContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.start`.
   * @param ctx the parse tree
   */
  exitStart?: (ctx: StartContext) => void;
  /**
   * Enter a parse tree produced by the `CommaExpressionWrapper3`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterCommaExpressionWrapper3?: (ctx: CommaExpressionWrapper3Context) => void;
  /**
   * Exit a parse tree produced by the `CommaExpressionWrapper3`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitCommaExpressionWrapper3?: (ctx: CommaExpressionWrapper3Context) => void;
  /**
   * Enter a parse tree produced by the `UpTraversalExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterUpTraversalExpression?: (ctx: UpTraversalExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `UpTraversalExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitUpTraversalExpression?: (ctx: UpTraversalExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `CommaExpressionWrapper2`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterCommaExpressionWrapper2?: (ctx: CommaExpressionWrapper2Context) => void;
  /**
   * Exit a parse tree produced by the `CommaExpressionWrapper2`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitCommaExpressionWrapper2?: (ctx: CommaExpressionWrapper2Context) => void;
  /**
   * Enter a parse tree produced by the `CommaExpressionWrapper1`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterCommaExpressionWrapper1?: (ctx: CommaExpressionWrapper1Context) => void;
  /**
   * Exit a parse tree produced by the `CommaExpressionWrapper1`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitCommaExpressionWrapper1?: (ctx: CommaExpressionWrapper1Context) => void;
  /**
   * Enter a parse tree produced by the `AllExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterAllExpression?: (ctx: AllExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `AllExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitAllExpression?: (ctx: AllExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `NotExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterNotExpression?: (ctx: NotExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `NotExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitNotExpression?: (ctx: NotExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `OrExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterOrExpression?: (ctx: OrExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `OrExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitOrExpression?: (ctx: OrExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `UpAndDownTraversalExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterUpAndDownTraversalExpression?: (ctx: UpAndDownTraversalExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `UpAndDownTraversalExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitUpAndDownTraversalExpression?: (ctx: UpAndDownTraversalExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `UnmatchedValue`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterUnmatchedValue?: (ctx: UnmatchedValueContext) => void;
  /**
   * Exit a parse tree produced by the `UnmatchedValue`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitUnmatchedValue?: (ctx: UnmatchedValueContext) => void;
  /**
   * Enter a parse tree produced by the `AndExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterAndExpression?: (ctx: AndExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `AndExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitAndExpression?: (ctx: AndExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `TraversalAllowedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterTraversalAllowedExpression?: (ctx: TraversalAllowedExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `TraversalAllowedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitTraversalAllowedExpression?: (ctx: TraversalAllowedExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `DownTraversalExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterDownTraversalExpression?: (ctx: DownTraversalExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `DownTraversalExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitDownTraversalExpression?: (ctx: DownTraversalExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `IncompleteOrExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterIncompleteOrExpression?: (ctx: IncompleteOrExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `IncompleteOrExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitIncompleteOrExpression?: (ctx: IncompleteOrExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `IncompleteNotExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterIncompleteNotExpression?: (ctx: IncompleteNotExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `IncompleteNotExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitIncompleteNotExpression?: (ctx: IncompleteNotExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `IncompleteAndExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  enterIncompleteAndExpression?: (ctx: IncompleteAndExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `IncompleteAndExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   */
  exitIncompleteAndExpression?: (ctx: IncompleteAndExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `AttributeExpression`
   * labeled alternative in `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  enterAttributeExpression?: (ctx: AttributeExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `AttributeExpression`
   * labeled alternative in `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  exitAttributeExpression?: (ctx: AttributeExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `FunctionCallExpression`
   * labeled alternative in `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  enterFunctionCallExpression?: (ctx: FunctionCallExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `FunctionCallExpression`
   * labeled alternative in `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  exitFunctionCallExpression?: (ctx: FunctionCallExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `TraversalAllowedParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  enterTraversalAllowedParenthesizedExpression?: (
    ctx: TraversalAllowedParenthesizedExpressionContext,
  ) => void;
  /**
   * Exit a parse tree produced by the `TraversalAllowedParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  exitTraversalAllowedParenthesizedExpression?: (
    ctx: TraversalAllowedParenthesizedExpressionContext,
  ) => void;
  /**
   * Enter a parse tree produced by the `IncompleteExpression`
   * labeled alternative in `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  enterIncompleteExpression?: (ctx: IncompleteExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `IncompleteExpression`
   * labeled alternative in `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   */
  exitIncompleteExpression?: (ctx: IncompleteExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `ParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.parenthesizedExpr`.
   * @param ctx the parse tree
   */
  enterParenthesizedExpression?: (ctx: ParenthesizedExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `ParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.parenthesizedExpr`.
   * @param ctx the parse tree
   */
  exitParenthesizedExpression?: (ctx: ParenthesizedExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `IncompleteAttributeExpressionMissingSecondValue`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  enterIncompleteAttributeExpressionMissingSecondValue?: (
    ctx: IncompleteAttributeExpressionMissingSecondValueContext,
  ) => void;
  /**
   * Exit a parse tree produced by the `IncompleteAttributeExpressionMissingSecondValue`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  exitIncompleteAttributeExpressionMissingSecondValue?: (
    ctx: IncompleteAttributeExpressionMissingSecondValueContext,
  ) => void;
  /**
   * Enter a parse tree produced by the `IncompleteAttributeExpressionMissingValue`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  enterIncompleteAttributeExpressionMissingValue?: (
    ctx: IncompleteAttributeExpressionMissingValueContext,
  ) => void;
  /**
   * Exit a parse tree produced by the `IncompleteAttributeExpressionMissingValue`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  exitIncompleteAttributeExpressionMissingValue?: (
    ctx: IncompleteAttributeExpressionMissingValueContext,
  ) => void;
  /**
   * Enter a parse tree produced by the `ExpressionlessFunctionExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  enterExpressionlessFunctionExpression?: (ctx: ExpressionlessFunctionExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `ExpressionlessFunctionExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  exitExpressionlessFunctionExpression?: (ctx: ExpressionlessFunctionExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `UnclosedExpressionlessFunctionExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  enterUnclosedExpressionlessFunctionExpression?: (
    ctx: UnclosedExpressionlessFunctionExpressionContext,
  ) => void;
  /**
   * Exit a parse tree produced by the `UnclosedExpressionlessFunctionExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  exitUnclosedExpressionlessFunctionExpression?: (
    ctx: UnclosedExpressionlessFunctionExpressionContext,
  ) => void;
  /**
   * Enter a parse tree produced by the `UnclosedFunctionExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  enterUnclosedFunctionExpression?: (ctx: UnclosedFunctionExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `UnclosedFunctionExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  exitUnclosedFunctionExpression?: (ctx: UnclosedFunctionExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `UnclosedParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  enterUnclosedParenthesizedExpression?: (ctx: UnclosedParenthesizedExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `UnclosedParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  exitUnclosedParenthesizedExpression?: (ctx: UnclosedParenthesizedExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `ExpressionlessParenthesizedExpressionWrapper`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  enterExpressionlessParenthesizedExpressionWrapper?: (
    ctx: ExpressionlessParenthesizedExpressionWrapperContext,
  ) => void;
  /**
   * Exit a parse tree produced by the `ExpressionlessParenthesizedExpressionWrapper`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  exitExpressionlessParenthesizedExpressionWrapper?: (
    ctx: ExpressionlessParenthesizedExpressionWrapperContext,
  ) => void;
  /**
   * Enter a parse tree produced by the `UnclosedExpressionlessParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  enterUnclosedExpressionlessParenthesizedExpression?: (
    ctx: UnclosedExpressionlessParenthesizedExpressionContext,
  ) => void;
  /**
   * Exit a parse tree produced by the `UnclosedExpressionlessParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  exitUnclosedExpressionlessParenthesizedExpression?: (
    ctx: UnclosedExpressionlessParenthesizedExpressionContext,
  ) => void;
  /**
   * Enter a parse tree produced by the `IncompletePlusTraversalExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  enterIncompletePlusTraversalExpression?: (ctx: IncompletePlusTraversalExpressionContext) => void;
  /**
   * Exit a parse tree produced by the `IncompletePlusTraversalExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  exitIncompletePlusTraversalExpression?: (ctx: IncompletePlusTraversalExpressionContext) => void;
  /**
   * Enter a parse tree produced by the `IncompletePlusTraversalExpressionMissingValue`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  enterIncompletePlusTraversalExpressionMissingValue?: (
    ctx: IncompletePlusTraversalExpressionMissingValueContext,
  ) => void;
  /**
   * Exit a parse tree produced by the `IncompletePlusTraversalExpressionMissingValue`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  exitIncompletePlusTraversalExpressionMissingValue?: (
    ctx: IncompletePlusTraversalExpressionMissingValueContext,
  ) => void;
  /**
   * Enter a parse tree produced by the `IncompleteAttributeExpressionMissingKey`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  enterIncompleteAttributeExpressionMissingKey?: (
    ctx: IncompleteAttributeExpressionMissingKeyContext,
  ) => void;
  /**
   * Exit a parse tree produced by the `IncompleteAttributeExpressionMissingKey`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   */
  exitIncompleteAttributeExpressionMissingKey?: (
    ctx: IncompleteAttributeExpressionMissingKeyContext,
  ) => void;
  /**
   * Enter a parse tree produced by the `ExpressionlessParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expressionLessParenthesizedExpr`.
   * @param ctx the parse tree
   */
  enterExpressionlessParenthesizedExpression?: (
    ctx: ExpressionlessParenthesizedExpressionContext,
  ) => void;
  /**
   * Exit a parse tree produced by the `ExpressionlessParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expressionLessParenthesizedExpr`.
   * @param ctx the parse tree
   */
  exitExpressionlessParenthesizedExpression?: (
    ctx: ExpressionlessParenthesizedExpressionContext,
  ) => void;
  /**
   * Enter a parse tree produced by the `UpTraversal`
   * labeled alternative in `SelectionAutoCompleteParser.upTraversalExpr`.
   * @param ctx the parse tree
   */
  enterUpTraversal?: (ctx: UpTraversalContext) => void;
  /**
   * Exit a parse tree produced by the `UpTraversal`
   * labeled alternative in `SelectionAutoCompleteParser.upTraversalExpr`.
   * @param ctx the parse tree
   */
  exitUpTraversal?: (ctx: UpTraversalContext) => void;
  /**
   * Enter a parse tree produced by the `DownTraversal`
   * labeled alternative in `SelectionAutoCompleteParser.downTraversalExpr`.
   * @param ctx the parse tree
   */
  enterDownTraversal?: (ctx: DownTraversalContext) => void;
  /**
   * Exit a parse tree produced by the `DownTraversal`
   * labeled alternative in `SelectionAutoCompleteParser.downTraversalExpr`.
   * @param ctx the parse tree
   */
  exitDownTraversal?: (ctx: DownTraversalContext) => void;
  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.upTraversalToken`.
   * @param ctx the parse tree
   */
  enterUpTraversalToken?: (ctx: UpTraversalTokenContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.upTraversalToken`.
   * @param ctx the parse tree
   */
  exitUpTraversalToken?: (ctx: UpTraversalTokenContext) => void;
  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.downTraversalToken`.
   * @param ctx the parse tree
   */
  enterDownTraversalToken?: (ctx: DownTraversalTokenContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.downTraversalToken`.
   * @param ctx the parse tree
   */
  exitDownTraversalToken?: (ctx: DownTraversalTokenContext) => void;
  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.attributeName`.
   * @param ctx the parse tree
   */
  enterAttributeName?: (ctx: AttributeNameContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.attributeName`.
   * @param ctx the parse tree
   */
  exitAttributeName?: (ctx: AttributeNameContext) => void;
  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.attributeValue`.
   * @param ctx the parse tree
   */
  enterAttributeValue?: (ctx: AttributeValueContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.attributeValue`.
   * @param ctx the parse tree
   */
  exitAttributeValue?: (ctx: AttributeValueContext) => void;
  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.functionName`.
   * @param ctx the parse tree
   */
  enterFunctionName?: (ctx: FunctionNameContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.functionName`.
   * @param ctx the parse tree
   */
  exitFunctionName?: (ctx: FunctionNameContext) => void;
  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.commaToken`.
   * @param ctx the parse tree
   */
  enterCommaToken?: (ctx: CommaTokenContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.commaToken`.
   * @param ctx the parse tree
   */
  exitCommaToken?: (ctx: CommaTokenContext) => void;
  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.orToken`.
   * @param ctx the parse tree
   */
  enterOrToken?: (ctx: OrTokenContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.orToken`.
   * @param ctx the parse tree
   */
  exitOrToken?: (ctx: OrTokenContext) => void;
  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.andToken`.
   * @param ctx the parse tree
   */
  enterAndToken?: (ctx: AndTokenContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.andToken`.
   * @param ctx the parse tree
   */
  exitAndToken?: (ctx: AndTokenContext) => void;
  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.notToken`.
   * @param ctx the parse tree
   */
  enterNotToken?: (ctx: NotTokenContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.notToken`.
   * @param ctx the parse tree
   */
  exitNotToken?: (ctx: NotTokenContext) => void;
  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.colonToken`.
   * @param ctx the parse tree
   */
  enterColonToken?: (ctx: ColonTokenContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.colonToken`.
   * @param ctx the parse tree
   */
  exitColonToken?: (ctx: ColonTokenContext) => void;
  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.leftParenToken`.
   * @param ctx the parse tree
   */
  enterLeftParenToken?: (ctx: LeftParenTokenContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.leftParenToken`.
   * @param ctx the parse tree
   */
  exitLeftParenToken?: (ctx: LeftParenTokenContext) => void;
  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.rightParenToken`.
   * @param ctx the parse tree
   */
  enterRightParenToken?: (ctx: RightParenTokenContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.rightParenToken`.
   * @param ctx the parse tree
   */
  exitRightParenToken?: (ctx: RightParenTokenContext) => void;
  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.attributeValueWhitespace`.
   * @param ctx the parse tree
   */
  enterAttributeValueWhitespace?: (ctx: AttributeValueWhitespaceContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.attributeValueWhitespace`.
   * @param ctx the parse tree
   */
  exitAttributeValueWhitespace?: (ctx: AttributeValueWhitespaceContext) => void;
  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.postAttributeValueWhitespace`.
   * @param ctx the parse tree
   */
  enterPostAttributeValueWhitespace?: (ctx: PostAttributeValueWhitespaceContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.postAttributeValueWhitespace`.
   * @param ctx the parse tree
   */
  exitPostAttributeValueWhitespace?: (ctx: PostAttributeValueWhitespaceContext) => void;
  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.postExpressionWhitespace`.
   * @param ctx the parse tree
   */
  enterPostExpressionWhitespace?: (ctx: PostExpressionWhitespaceContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.postExpressionWhitespace`.
   * @param ctx the parse tree
   */
  exitPostExpressionWhitespace?: (ctx: PostExpressionWhitespaceContext) => void;
  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.postNotOperatorWhitespace`.
   * @param ctx the parse tree
   */
  enterPostNotOperatorWhitespace?: (ctx: PostNotOperatorWhitespaceContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.postNotOperatorWhitespace`.
   * @param ctx the parse tree
   */
  exitPostNotOperatorWhitespace?: (ctx: PostNotOperatorWhitespaceContext) => void;
  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.postLogicalOperatorWhitespace`.
   * @param ctx the parse tree
   */
  enterPostLogicalOperatorWhitespace?: (ctx: PostLogicalOperatorWhitespaceContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.postLogicalOperatorWhitespace`.
   * @param ctx the parse tree
   */
  exitPostLogicalOperatorWhitespace?: (ctx: PostLogicalOperatorWhitespaceContext) => void;
  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.postNeighborTraversalWhitespace`.
   * @param ctx the parse tree
   */
  enterPostNeighborTraversalWhitespace?: (ctx: PostNeighborTraversalWhitespaceContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.postNeighborTraversalWhitespace`.
   * @param ctx the parse tree
   */
  exitPostNeighborTraversalWhitespace?: (ctx: PostNeighborTraversalWhitespaceContext) => void;
  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.postUpwardTraversalWhitespace`.
   * @param ctx the parse tree
   */
  enterPostUpwardTraversalWhitespace?: (ctx: PostUpwardTraversalWhitespaceContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.postUpwardTraversalWhitespace`.
   * @param ctx the parse tree
   */
  exitPostUpwardTraversalWhitespace?: (ctx: PostUpwardTraversalWhitespaceContext) => void;
  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.postDownwardTraversalWhitespace`.
   * @param ctx the parse tree
   */
  enterPostDownwardTraversalWhitespace?: (ctx: PostDownwardTraversalWhitespaceContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.postDownwardTraversalWhitespace`.
   * @param ctx the parse tree
   */
  exitPostDownwardTraversalWhitespace?: (ctx: PostDownwardTraversalWhitespaceContext) => void;
  /**
   * Enter a parse tree produced by `SelectionAutoCompleteParser.postDigitsWhitespace`.
   * @param ctx the parse tree
   */
  enterPostDigitsWhitespace?: (ctx: PostDigitsWhitespaceContext) => void;
  /**
   * Exit a parse tree produced by `SelectionAutoCompleteParser.postDigitsWhitespace`.
   * @param ctx the parse tree
   */
  exitPostDigitsWhitespace?: (ctx: PostDigitsWhitespaceContext) => void;
  /**
   * Enter a parse tree produced by the `QuotedStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   */
  enterQuotedStringValue?: (ctx: QuotedStringValueContext) => void;
  /**
   * Exit a parse tree produced by the `QuotedStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   */
  exitQuotedStringValue?: (ctx: QuotedStringValueContext) => void;
  /**
   * Enter a parse tree produced by the `IncompleteLeftQuotedStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   */
  enterIncompleteLeftQuotedStringValue?: (ctx: IncompleteLeftQuotedStringValueContext) => void;
  /**
   * Exit a parse tree produced by the `IncompleteLeftQuotedStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   */
  exitIncompleteLeftQuotedStringValue?: (ctx: IncompleteLeftQuotedStringValueContext) => void;
  /**
   * Enter a parse tree produced by the `IncompleteRightQuotedStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   */
  enterIncompleteRightQuotedStringValue?: (ctx: IncompleteRightQuotedStringValueContext) => void;
  /**
   * Exit a parse tree produced by the `IncompleteRightQuotedStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   */
  exitIncompleteRightQuotedStringValue?: (ctx: IncompleteRightQuotedStringValueContext) => void;
  /**
   * Enter a parse tree produced by the `UnquotedStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   */
  enterUnquotedStringValue?: (ctx: UnquotedStringValueContext) => void;
  /**
   * Exit a parse tree produced by the `UnquotedStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   */
  exitUnquotedStringValue?: (ctx: UnquotedStringValueContext) => void;
  /**
   * Enter a parse tree produced by the `NullStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   */
  enterNullStringValue?: (ctx: NullStringValueContext) => void;
  /**
   * Exit a parse tree produced by the `NullStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   */
  exitNullStringValue?: (ctx: NullStringValueContext) => void;
  /**
   * Enter a parse tree produced by the `DigitsValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   */
  enterDigitsValue?: (ctx: DigitsValueContext) => void;
  /**
   * Exit a parse tree produced by the `DigitsValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   */
  exitDigitsValue?: (ctx: DigitsValueContext) => void;

  visitTerminal(node: TerminalNode): void {}
  visitErrorNode(node: ErrorNode): void {}
  enterEveryRule(node: ParserRuleContext): void {}
  exitEveryRule(node: ParserRuleContext): void {}
}
