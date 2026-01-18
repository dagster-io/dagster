// Generated from /home/user/dagster/js_modules/dagster-ui/packages/ui-core/src/selection/SelectionAutoComplete.g4 by ANTLR 4.13.1

import {AbstractParseTreeVisitor} from 'antlr4ng';

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
 * This interface defines a complete generic visitor for a parse tree produced
 * by `SelectionAutoCompleteParser`.
 *
 * @param <Result> The return type of the visit operation. Use `void` for
 * operations with no return type.
 */
export class SelectionAutoCompleteVisitor<Result> extends AbstractParseTreeVisitor<Result> {
  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.start`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitStart?: (ctx: StartContext) => Result;
  /**
   * Visit a parse tree produced by the `CommaExpressionWrapper3`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitCommaExpressionWrapper3?: (ctx: CommaExpressionWrapper3Context) => Result;
  /**
   * Visit a parse tree produced by the `UpTraversalExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUpTraversalExpression?: (ctx: UpTraversalExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `CommaExpressionWrapper2`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitCommaExpressionWrapper2?: (ctx: CommaExpressionWrapper2Context) => Result;
  /**
   * Visit a parse tree produced by the `CommaExpressionWrapper1`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitCommaExpressionWrapper1?: (ctx: CommaExpressionWrapper1Context) => Result;
  /**
   * Visit a parse tree produced by the `AllExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAllExpression?: (ctx: AllExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `NotExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitNotExpression?: (ctx: NotExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `OrExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitOrExpression?: (ctx: OrExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `UpAndDownTraversalExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUpAndDownTraversalExpression?: (ctx: UpAndDownTraversalExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `UnmatchedValue`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUnmatchedValue?: (ctx: UnmatchedValueContext) => Result;
  /**
   * Visit a parse tree produced by the `AndExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAndExpression?: (ctx: AndExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `TraversalAllowedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitTraversalAllowedExpression?: (ctx: TraversalAllowedExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `DownTraversalExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitDownTraversalExpression?: (ctx: DownTraversalExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `IncompleteOrExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitIncompleteOrExpression?: (ctx: IncompleteOrExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `IncompleteNotExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitIncompleteNotExpression?: (ctx: IncompleteNotExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `IncompleteAndExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitIncompleteAndExpression?: (ctx: IncompleteAndExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `AttributeExpression`
   * labeled alternative in `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAttributeExpression?: (ctx: AttributeExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `FunctionCallExpression`
   * labeled alternative in `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitFunctionCallExpression?: (ctx: FunctionCallExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `TraversalAllowedParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitTraversalAllowedParenthesizedExpression?: (
    ctx: TraversalAllowedParenthesizedExpressionContext,
  ) => Result;
  /**
   * Visit a parse tree produced by the `IncompleteExpression`
   * labeled alternative in `SelectionAutoCompleteParser.traversalAllowedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitIncompleteExpression?: (ctx: IncompleteExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `ParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.parenthesizedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitParenthesizedExpression?: (ctx: ParenthesizedExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `IncompleteAttributeExpressionMissingSecondValue`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitIncompleteAttributeExpressionMissingSecondValue?: (
    ctx: IncompleteAttributeExpressionMissingSecondValueContext,
  ) => Result;
  /**
   * Visit a parse tree produced by the `IncompleteAttributeExpressionMissingValue`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitIncompleteAttributeExpressionMissingValue?: (
    ctx: IncompleteAttributeExpressionMissingValueContext,
  ) => Result;
  /**
   * Visit a parse tree produced by the `ExpressionlessFunctionExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitExpressionlessFunctionExpression?: (ctx: ExpressionlessFunctionExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `UnclosedExpressionlessFunctionExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUnclosedExpressionlessFunctionExpression?: (
    ctx: UnclosedExpressionlessFunctionExpressionContext,
  ) => Result;
  /**
   * Visit a parse tree produced by the `UnclosedFunctionExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUnclosedFunctionExpression?: (ctx: UnclosedFunctionExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `UnclosedParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUnclosedParenthesizedExpression?: (ctx: UnclosedParenthesizedExpressionContext) => Result;
  /**
   * Visit a parse tree produced by the `ExpressionlessParenthesizedExpressionWrapper`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitExpressionlessParenthesizedExpressionWrapper?: (
    ctx: ExpressionlessParenthesizedExpressionWrapperContext,
  ) => Result;
  /**
   * Visit a parse tree produced by the `UnclosedExpressionlessParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUnclosedExpressionlessParenthesizedExpression?: (
    ctx: UnclosedExpressionlessParenthesizedExpressionContext,
  ) => Result;
  /**
   * Visit a parse tree produced by the `IncompletePlusTraversalExpression`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitIncompletePlusTraversalExpression?: (
    ctx: IncompletePlusTraversalExpressionContext,
  ) => Result;
  /**
   * Visit a parse tree produced by the `IncompletePlusTraversalExpressionMissingValue`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitIncompletePlusTraversalExpressionMissingValue?: (
    ctx: IncompletePlusTraversalExpressionMissingValueContext,
  ) => Result;
  /**
   * Visit a parse tree produced by the `IncompleteAttributeExpressionMissingKey`
   * labeled alternative in `SelectionAutoCompleteParser.incompleteExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitIncompleteAttributeExpressionMissingKey?: (
    ctx: IncompleteAttributeExpressionMissingKeyContext,
  ) => Result;
  /**
   * Visit a parse tree produced by the `ExpressionlessParenthesizedExpression`
   * labeled alternative in `SelectionAutoCompleteParser.expressionLessParenthesizedExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitExpressionlessParenthesizedExpression?: (
    ctx: ExpressionlessParenthesizedExpressionContext,
  ) => Result;
  /**
   * Visit a parse tree produced by the `UpTraversal`
   * labeled alternative in `SelectionAutoCompleteParser.upTraversalExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUpTraversal?: (ctx: UpTraversalContext) => Result;
  /**
   * Visit a parse tree produced by the `DownTraversal`
   * labeled alternative in `SelectionAutoCompleteParser.downTraversalExpr`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitDownTraversal?: (ctx: DownTraversalContext) => Result;
  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.upTraversalToken`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUpTraversalToken?: (ctx: UpTraversalTokenContext) => Result;
  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.downTraversalToken`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitDownTraversalToken?: (ctx: DownTraversalTokenContext) => Result;
  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.attributeName`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAttributeName?: (ctx: AttributeNameContext) => Result;
  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.attributeValue`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAttributeValue?: (ctx: AttributeValueContext) => Result;
  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.functionName`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitFunctionName?: (ctx: FunctionNameContext) => Result;
  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.commaToken`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitCommaToken?: (ctx: CommaTokenContext) => Result;
  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.orToken`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitOrToken?: (ctx: OrTokenContext) => Result;
  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.andToken`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAndToken?: (ctx: AndTokenContext) => Result;
  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.notToken`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitNotToken?: (ctx: NotTokenContext) => Result;
  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.colonToken`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitColonToken?: (ctx: ColonTokenContext) => Result;
  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.leftParenToken`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitLeftParenToken?: (ctx: LeftParenTokenContext) => Result;
  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.rightParenToken`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitRightParenToken?: (ctx: RightParenTokenContext) => Result;
  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.attributeValueWhitespace`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitAttributeValueWhitespace?: (ctx: AttributeValueWhitespaceContext) => Result;
  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.postAttributeValueWhitespace`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitPostAttributeValueWhitespace?: (ctx: PostAttributeValueWhitespaceContext) => Result;
  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.postExpressionWhitespace`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitPostExpressionWhitespace?: (ctx: PostExpressionWhitespaceContext) => Result;
  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.postNotOperatorWhitespace`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitPostNotOperatorWhitespace?: (ctx: PostNotOperatorWhitespaceContext) => Result;
  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.postLogicalOperatorWhitespace`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitPostLogicalOperatorWhitespace?: (ctx: PostLogicalOperatorWhitespaceContext) => Result;
  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.postNeighborTraversalWhitespace`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitPostNeighborTraversalWhitespace?: (ctx: PostNeighborTraversalWhitespaceContext) => Result;
  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.postUpwardTraversalWhitespace`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitPostUpwardTraversalWhitespace?: (ctx: PostUpwardTraversalWhitespaceContext) => Result;
  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.postDownwardTraversalWhitespace`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitPostDownwardTraversalWhitespace?: (ctx: PostDownwardTraversalWhitespaceContext) => Result;
  /**
   * Visit a parse tree produced by `SelectionAutoCompleteParser.postDigitsWhitespace`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitPostDigitsWhitespace?: (ctx: PostDigitsWhitespaceContext) => Result;
  /**
   * Visit a parse tree produced by the `QuotedStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitQuotedStringValue?: (ctx: QuotedStringValueContext) => Result;
  /**
   * Visit a parse tree produced by the `IncompleteLeftQuotedStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitIncompleteLeftQuotedStringValue?: (ctx: IncompleteLeftQuotedStringValueContext) => Result;
  /**
   * Visit a parse tree produced by the `IncompleteRightQuotedStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitIncompleteRightQuotedStringValue?: (ctx: IncompleteRightQuotedStringValueContext) => Result;
  /**
   * Visit a parse tree produced by the `UnquotedStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUnquotedStringValue?: (ctx: UnquotedStringValueContext) => Result;
  /**
   * Visit a parse tree produced by the `NullStringValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitNullStringValue?: (ctx: NullStringValueContext) => Result;
  /**
   * Visit a parse tree produced by the `DigitsValue`
   * labeled alternative in `SelectionAutoCompleteParser.value`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitDigitsValue?: (ctx: DigitsValueContext) => Result;
}
