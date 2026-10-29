import {AbstractParseTreeVisitor, ParseTree, Trees} from 'antlr4ng';

import {getLeadingWhitespaceLength, parseInput} from '../selection/SelectionInputParser';
import {getValueNodeValue} from '../selection/SelectionInputUtil';
import {
  CommaTokenContext,
  IncompleteLeftQuotedStringValueContext,
  IncompleteRightQuotedStringValueContext,
  UnmatchedValueContext,
  UnquotedRejectedValueContext,
} from '../selection/generated/SelectionAutoCompleteParser';
import {SelectionAutoCompleteVisitor} from '../selection/generated/SelectionAutoCompleteVisitor';

// The grammar's `WS` characters, not JavaScript's wider `\s`.
const LEADING_WHITESPACE = /^[ \t\r\n]+/;
const TRAILING_WHITESPACE = /[ \t\r\n]+$/;

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
    const valueCtx = ctx.value();
    if (!valueCtx) {
      return;
    }
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const originalStart = valueCtx.start!.start;
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const originalEnd = valueCtx.stop!.stop;

    const currentStart = originalStart + this.offset;
    const currentEnd = originalEnd + this.offset;

    const value = getValueNodeValue(valueCtx);
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
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const start = ctx.start!.start + this.offset;
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const end = ctx.stop!.stop + this.offset;

    // Remove the grammar's whitespace around the comma and replace with ' or '
    const before = this.convertedQuery.slice(0, start).replace(TRAILING_WHITESPACE, '');
    const after = this.convertedQuery.slice(end + 1).replace(LEADING_WHITESPACE, '');
    const previousLength = this.convertedQuery.length;
    this.convertedQuery = before + ' or ' + after;

    // Count the trimmed spaces too, not just the comma becoming ' or '
    this.offset += this.convertedQuery.length - previousLength;
  }
}

// Wrapping a bare value with no letter or digit, or with a hidden character, would make it valid
// but match nothing, so it stays as typed for the linter to flag.
const isUnwrappableValue = (node: ParseTree) => {
  if (
    !(node instanceof UnquotedRejectedValueContext) ||
    !(node.parent instanceof UnmatchedValueContext)
  ) {
    return false;
  }
  const text = node.getText();
  return !/[\p{L}\p{N}]/u.test(text) || /[\p{C}\p{Z}]/u.test(text);
};

const isIncompleteQuotedValue = (node: ParseTree) =>
  node instanceof IncompleteLeftQuotedStringValueContext ||
  node instanceof IncompleteRightQuotedStringValueContext;

// Joining these trees with ` or ` changes what the query means: touching terms (`my-func(key:a)`)
// or a traversal count split from its term (`key:a+ 2`).
const isUnsafeBoundary = (line: string, nextLine: string) =>
  !TRAILING_WHITESPACE.test(line) || /\+[ \t\r\n]*$/.test(line) || nextLine.startsWith('+');

/**
 * Whether upgrading would rewrite the query into one that lints clean but means something else.
 * Rewrites that fail the page's linter are caught where the input commits.
 */
const shouldKeepAsTyped = (query: string, parseTrees: {tree: ParseTree; line: string}[]) => {
  const lines = parseTrees.map(({line}) => line);
  const nodes = parseTrees.flatMap(({tree}) => Trees.descendants(tree));
  const treesBeforeLast = parseTrees.slice(0, -1);

  const coversQuery = lines.join('') === query.slice(getLeadingWhitespaceLength(query));
  const hasUnwrappableValue = nodes.some(isUnwrappableValue);
  const hasOpenQuoteBeforeAnotherTree = treesBeforeLast.some(({tree}) =>
    Trees.descendants(tree).some(isIncompleteQuotedValue),
  );
  const hasUnsafeBoundary = lines
    .slice(0, -1)
    .some((line, index) => isUnsafeBoundary(line, lines[index + 1] ?? ''));

  return !coversQuery || hasUnwrappableValue || hasOpenQuoteBeforeAnotherTree || hasUnsafeBoundary;
};

// Convert unmatched values to wildcard substring matches for the given attribute name
// and convert commas to OR operators
export const upgradeSyntax = (query: string, attributeName: string) => {
  try {
    const {parseTrees} = parseInput(query);
    if (shouldKeepAsTyped(query, parseTrees)) {
      return query;
    }

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
