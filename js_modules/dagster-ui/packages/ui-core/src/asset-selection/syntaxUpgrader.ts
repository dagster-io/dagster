import {AbstractParseTreeVisitor} from 'antlr4ts/tree/AbstractParseTreeVisitor';

import {parseInput} from '../selection/SelectionInputParser';
import {getValueNodeValue} from '../selection/SelectionInputUtil';
import {
  CommaTokenContext,
  UnmatchedValueContext,
} from '../selection/generated/SelectionAutoCompleteParser';
import {SelectionAutoCompleteVisitor} from '../selection/generated/SelectionAutoCompleteVisitor';

class SyntaxUpgradingVisitor
  extends AbstractParseTreeVisitor<void>
  implements SelectionAutoCompleteVisitor<void>
{
  public convertedQuery: string;
  private offset: number;

  constructor(
    query: string,
    private attributeName: string,
  ) {
    super();
    this.offset = 0;
    this.convertedQuery = query;
  }
  defaultResult() {}

  visitUnmatchedValue(ctx: UnmatchedValueContext) {
    const originalStart = ctx.value().start!.startIndex;
    const originalEnd = ctx.value().stop!.stopIndex;

    const currentStart = originalStart + this.offset;
    const currentEnd = originalEnd + this.offset;

    const value = getValueNodeValue(ctx.value());
    const converted = `${this.attributeName}:"*${value}*"`;

    // Update the converted query
    this.convertedQuery =
      this.convertedQuery.slice(0, currentStart) +
      converted +
      this.convertedQuery.slice(currentEnd + 1);

    const originalLength = originalEnd - originalStart + 1;
    const convertedLength = converted.length;
    const lengthDiff = convertedLength - originalLength;
    this.offset += lengthDiff;
  }

  visitCommaToken(ctx: CommaTokenContext) {
    const start = ctx.start.startIndex + this.offset;
    const end = ctx.stop!.stopIndex + this.offset;

    // Remove any spaces around the comma and replace with ' or '
    const before = this.convertedQuery.slice(0, start).trimEnd();
    const after = this.convertedQuery.slice(end + 1).trimStart();
    this.convertedQuery = before + ' or ' + after;

    // Update offset by the difference between ' or ' (4 chars) and ',' (1 char)
    // plus any spaces we removed
    const originalLength = end - start + 1;
    const newLength = 4;
    this.offset += newLength - originalLength;
  }
}

// Convert unmatched values to wildcard substring matches for the given attribute name
// and convert commas to OR operators
export const upgradeSyntax = (query: string, attributeName: string) => {
  try {
    const {parseTrees} = parseInput(query);

    let convertedQuery = '';
    const numberOfTrees = parseTrees.length;
    parseTrees.forEach(({tree, line}, index) => {
      const visitor = new SyntaxUpgradingVisitor(line, attributeName);
      visitor.visit(tree);
      convertedQuery += visitor.convertedQuery;
      if (index < numberOfTrees - 1) {
        convertedQuery += ' or ';
      }
    });
    return convertedQuery;
  } catch (error) {
    console.error('Error upgrading syntax', error);
    return query;
  }
};
