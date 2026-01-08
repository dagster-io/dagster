import {AbstractParseTreeVisitor} from 'antlr4ts/tree/AbstractParseTreeVisitor';

import {
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
} from './generated/PartitionSelectionParser';
import {PartitionSelectionVisitor} from './generated/PartitionSelectionVisitor';

/**
 * Represents a parsed partition selection term.
 */
export type ParsedPartitionTerm =
  | {type: 'range'; start: string; end: string}
  | {type: 'wildcard'; prefix: string; suffix: string}
  | {type: 'single'; key: string};

/**
 * ANTLR visitor that transforms a partition selection parse tree into
 * an array of ParsedPartitionTerm objects.
 */
export class AntlrPartitionSelectionVisitor
  extends AbstractParseTreeVisitor<ParsedPartitionTerm[]>
  implements PartitionSelectionVisitor<ParsedPartitionTerm[]>
{
  protected defaultResult(): ParsedPartitionTerm[] {
    return [];
  }

  protected aggregateResult(
    aggregate: ParsedPartitionTerm[],
    nextResult: ParsedPartitionTerm[],
  ): ParsedPartitionTerm[] {
    return [...aggregate, ...nextResult];
  }

  visitStart(ctx: StartContext): ParsedPartitionTerm[] {
    const partitionList = ctx.partitionList();
    if (partitionList) {
      return this.visit(partitionList);
    }
    return [];
  }

  visitPartitionList(ctx: PartitionListContext): ParsedPartitionTerm[] {
    return ctx.partitionItem().flatMap((item) => this.visit(item));
  }

  visitRangePartitionItem(ctx: RangePartitionItemContext): ParsedPartitionTerm[] {
    return this.visit(ctx.range());
  }

  visitWildcardPartitionItem(ctx: WildcardPartitionItemContext): ParsedPartitionTerm[] {
    return this.visit(ctx.wildcard());
  }

  visitSinglePartitionItem(ctx: SinglePartitionItemContext): ParsedPartitionTerm[] {
    const key = this.extractPartitionKey(ctx.partitionKey());
    return [{type: 'single', key}];
  }

  visitRange(ctx: RangeContext): ParsedPartitionTerm[] {
    const keys = ctx.partitionKey();
    const startKey = keys[0];
    const endKey = keys[1];
    if (!startKey || !endKey) {
      // Should not happen with valid grammar, but handle gracefully
      return [];
    }
    const start = this.extractPartitionKey(startKey);
    const end = this.extractPartitionKey(endKey);
    return [{type: 'range', start, end}];
  }

  visitWildcard(ctx: WildcardContext): ParsedPartitionTerm[] {
    const pattern = ctx.WILDCARD_PATTERN().text;
    const asteriskIndex = pattern.indexOf('*');
    return [
      {
        type: 'wildcard',
        prefix: pattern.substring(0, asteriskIndex),
        suffix: pattern.substring(asteriskIndex + 1),
      },
    ];
  }

  /**
   * Extract the actual partition key string from a PartitionKeyContext.
   * Handles both quoted and unquoted keys.
   */
  private extractPartitionKey(ctx: PartitionKeyContext): string {
    if (ctx instanceof QuotedPartitionKeyContext) {
      const quoted = ctx.QUOTED_STRING().text;
      return this.unescapeQuotedString(quoted);
    }
    if (ctx instanceof UnquotedPartitionKeyContext) {
      return ctx.UNQUOTED_STRING().text;
    }
    // Fallback - should not happen with valid grammar
    return ctx.text;
  }

  /**
   * Remove surrounding quotes and unescape escape sequences.
   * Handles: \" -> ", \\ -> \, \/ -> /
   */
  private unescapeQuotedString(quoted: string): string {
    // Remove surrounding quotes
    const inner = quoted.slice(1, -1);
    // Unescape sequences: \" -> ", \\ -> \, \/ -> /
    return inner.replace(/\\(["\\/])/g, '$1');
  }
}
