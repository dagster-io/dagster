// Generated from /home/user/dagster/js_modules/dagster-ui/packages/ui-core/src/partitions/PartitionSelection.g4 by ANTLR 4.13.1

import {AbstractParseTreeVisitor} from 'antlr4ng';

import {StartContext} from './PartitionSelectionParser.js';
import {PartitionListContext} from './PartitionSelectionParser.js';
import {RangePartitionItemContext} from './PartitionSelectionParser.js';
import {WildcardPartitionItemContext} from './PartitionSelectionParser.js';
import {SinglePartitionItemContext} from './PartitionSelectionParser.js';
import {RangeContext} from './PartitionSelectionParser.js';
import {WildcardContext} from './PartitionSelectionParser.js';
import {QuotedPartitionKeyContext} from './PartitionSelectionParser.js';
import {UnquotedPartitionKeyContext} from './PartitionSelectionParser.js';

/**
 * This interface defines a complete generic visitor for a parse tree produced
 * by `PartitionSelectionParser`.
 *
 * @param <Result> The return type of the visit operation. Use `void` for
 * operations with no return type.
 */
export class PartitionSelectionVisitor<Result> extends AbstractParseTreeVisitor<Result> {
  /**
   * Visit a parse tree produced by `PartitionSelectionParser.start`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitStart?: (ctx: StartContext) => Result;
  /**
   * Visit a parse tree produced by `PartitionSelectionParser.partitionList`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitPartitionList?: (ctx: PartitionListContext) => Result;
  /**
   * Visit a parse tree produced by the `RangePartitionItem`
   * labeled alternative in `PartitionSelectionParser.partitionItem`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitRangePartitionItem?: (ctx: RangePartitionItemContext) => Result;
  /**
   * Visit a parse tree produced by the `WildcardPartitionItem`
   * labeled alternative in `PartitionSelectionParser.partitionItem`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitWildcardPartitionItem?: (ctx: WildcardPartitionItemContext) => Result;
  /**
   * Visit a parse tree produced by the `SinglePartitionItem`
   * labeled alternative in `PartitionSelectionParser.partitionItem`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitSinglePartitionItem?: (ctx: SinglePartitionItemContext) => Result;
  /**
   * Visit a parse tree produced by `PartitionSelectionParser.range`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitRange?: (ctx: RangeContext) => Result;
  /**
   * Visit a parse tree produced by `PartitionSelectionParser.wildcard`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitWildcard?: (ctx: WildcardContext) => Result;
  /**
   * Visit a parse tree produced by the `QuotedPartitionKey`
   * labeled alternative in `PartitionSelectionParser.partitionKey`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitQuotedPartitionKey?: (ctx: QuotedPartitionKeyContext) => Result;
  /**
   * Visit a parse tree produced by the `UnquotedPartitionKey`
   * labeled alternative in `PartitionSelectionParser.partitionKey`.
   * @param ctx the parse tree
   * @return the visitor result
   */
  visitUnquotedPartitionKey?: (ctx: UnquotedPartitionKeyContext) => Result;
}
