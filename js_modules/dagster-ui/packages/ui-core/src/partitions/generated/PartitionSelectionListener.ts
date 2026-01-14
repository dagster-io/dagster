// Generated from /home/user/dagster/js_modules/dagster-ui/packages/ui-core/src/partitions/PartitionSelection.g4 by ANTLR 4.9.0-SNAPSHOT

import {ParseTreeListener} from 'antlr4ts/tree/ParseTreeListener';

import {
  PartitionItemContext,
  PartitionKeyContext,
  PartitionListContext,
  QuotedPartitionKeyContext,
  RangeContext,
  RangePartitionItemContext,
  SinglePartitionItemContext,
  StartContext,
  UnquotedPartitionKeyContext,
  WildcardContext,
  WildcardPartitionItemContext,
} from './PartitionSelectionParser';

/**
 * This interface defines a complete listener for a parse tree produced by
 * `PartitionSelectionParser`.
 */
export interface PartitionSelectionListener extends ParseTreeListener {
  /**
   * Enter a parse tree produced by the `QuotedPartitionKey`
   * labeled alternative in `PartitionSelectionParser.partitionKey`.
   * @param ctx the parse tree
   */
  enterQuotedPartitionKey?: (ctx: QuotedPartitionKeyContext) => void;
  /**
   * Exit a parse tree produced by the `QuotedPartitionKey`
   * labeled alternative in `PartitionSelectionParser.partitionKey`.
   * @param ctx the parse tree
   */
  exitQuotedPartitionKey?: (ctx: QuotedPartitionKeyContext) => void;

  /**
   * Enter a parse tree produced by the `UnquotedPartitionKey`
   * labeled alternative in `PartitionSelectionParser.partitionKey`.
   * @param ctx the parse tree
   */
  enterUnquotedPartitionKey?: (ctx: UnquotedPartitionKeyContext) => void;
  /**
   * Exit a parse tree produced by the `UnquotedPartitionKey`
   * labeled alternative in `PartitionSelectionParser.partitionKey`.
   * @param ctx the parse tree
   */
  exitUnquotedPartitionKey?: (ctx: UnquotedPartitionKeyContext) => void;

  /**
   * Enter a parse tree produced by the `RangePartitionItem`
   * labeled alternative in `PartitionSelectionParser.partitionItem`.
   * @param ctx the parse tree
   */
  enterRangePartitionItem?: (ctx: RangePartitionItemContext) => void;
  /**
   * Exit a parse tree produced by the `RangePartitionItem`
   * labeled alternative in `PartitionSelectionParser.partitionItem`.
   * @param ctx the parse tree
   */
  exitRangePartitionItem?: (ctx: RangePartitionItemContext) => void;

  /**
   * Enter a parse tree produced by the `WildcardPartitionItem`
   * labeled alternative in `PartitionSelectionParser.partitionItem`.
   * @param ctx the parse tree
   */
  enterWildcardPartitionItem?: (ctx: WildcardPartitionItemContext) => void;
  /**
   * Exit a parse tree produced by the `WildcardPartitionItem`
   * labeled alternative in `PartitionSelectionParser.partitionItem`.
   * @param ctx the parse tree
   */
  exitWildcardPartitionItem?: (ctx: WildcardPartitionItemContext) => void;

  /**
   * Enter a parse tree produced by the `SinglePartitionItem`
   * labeled alternative in `PartitionSelectionParser.partitionItem`.
   * @param ctx the parse tree
   */
  enterSinglePartitionItem?: (ctx: SinglePartitionItemContext) => void;
  /**
   * Exit a parse tree produced by the `SinglePartitionItem`
   * labeled alternative in `PartitionSelectionParser.partitionItem`.
   * @param ctx the parse tree
   */
  exitSinglePartitionItem?: (ctx: SinglePartitionItemContext) => void;

  /**
   * Enter a parse tree produced by `PartitionSelectionParser.start`.
   * @param ctx the parse tree
   */
  enterStart?: (ctx: StartContext) => void;
  /**
   * Exit a parse tree produced by `PartitionSelectionParser.start`.
   * @param ctx the parse tree
   */
  exitStart?: (ctx: StartContext) => void;

  /**
   * Enter a parse tree produced by `PartitionSelectionParser.partitionList`.
   * @param ctx the parse tree
   */
  enterPartitionList?: (ctx: PartitionListContext) => void;
  /**
   * Exit a parse tree produced by `PartitionSelectionParser.partitionList`.
   * @param ctx the parse tree
   */
  exitPartitionList?: (ctx: PartitionListContext) => void;

  /**
   * Enter a parse tree produced by `PartitionSelectionParser.partitionItem`.
   * @param ctx the parse tree
   */
  enterPartitionItem?: (ctx: PartitionItemContext) => void;
  /**
   * Exit a parse tree produced by `PartitionSelectionParser.partitionItem`.
   * @param ctx the parse tree
   */
  exitPartitionItem?: (ctx: PartitionItemContext) => void;

  /**
   * Enter a parse tree produced by `PartitionSelectionParser.range`.
   * @param ctx the parse tree
   */
  enterRange?: (ctx: RangeContext) => void;
  /**
   * Exit a parse tree produced by `PartitionSelectionParser.range`.
   * @param ctx the parse tree
   */
  exitRange?: (ctx: RangeContext) => void;

  /**
   * Enter a parse tree produced by `PartitionSelectionParser.wildcard`.
   * @param ctx the parse tree
   */
  enterWildcard?: (ctx: WildcardContext) => void;
  /**
   * Exit a parse tree produced by `PartitionSelectionParser.wildcard`.
   * @param ctx the parse tree
   */
  exitWildcard?: (ctx: WildcardContext) => void;

  /**
   * Enter a parse tree produced by `PartitionSelectionParser.partitionKey`.
   * @param ctx the parse tree
   */
  enterPartitionKey?: (ctx: PartitionKeyContext) => void;
  /**
   * Exit a parse tree produced by `PartitionSelectionParser.partitionKey`.
   * @param ctx the parse tree
   */
  exitPartitionKey?: (ctx: PartitionKeyContext) => void;
}
