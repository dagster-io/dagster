import {BaseErrorListener, CharStream, CommonTokenStream, RecognitionException, Token} from 'antlr4ng';

import {
  AntlrPartitionSelectionVisitor,
  ParsedPartitionTerm,
} from './AntlrPartitionSelectionVisitor';
import {PartitionSelectionLexer} from './generated/PartitionSelectionLexer';
import {PartitionSelectionParser} from './generated/PartitionSelectionParser';

/**
 * Error thrown when partition selection parsing fails.
 */
export class PartitionSelectionParseError extends Error {
  constructor(
    message: string,
    public readonly position: number,
  ) {
    super(message);
    this.name = 'PartitionSelectionParseError';
  }
}

/**
 * Error listener that collects syntax errors during parsing.
 */
class PartitionSelectionErrorListener extends BaseErrorListener {
  errors: PartitionSelectionParseError[] = [];

  override syntaxError(
    _recognizer: unknown,
    offendingSymbol: Token | null,
    _line: number,
    charPositionInLine: number,
    msg: string,
    _e: RecognitionException | null,
  ): void {
    const errorMsg = offendingSymbol
      ? `Syntax error at "${offendingSymbol.text}": ${msg}`
      : `Syntax error at position ${charPositionInLine}: ${msg}`;
    this.errors.push(new PartitionSelectionParseError(errorMsg, charPositionInLine));
  }
}

/**
 * Parse a partition selection string into structured terms.
 *
 * Supported syntax:
 * - Single keys: `partition1`, `"key,with,commas"`
 * - Ranges: `[2024-01-01...2024-12-31]`, `["start"..."end"]`
 * - Wildcards: `2024-*`, `*-suffix`
 * - Lists: `key1, key2, [range1...range2]`
 *
 * Quoted strings support escape sequences:
 * - `\"` for literal quote
 * - `\\` for literal backslash
 * - `\/` for literal forward slash
 *
 * @param text The partition selection string to parse
 * @returns Array of parsed terms, or Error if parsing fails
 *
 * @example
 * // Simple unquoted keys
 * parsePartitionSelection('2024-01-01')
 * // => [{type: 'single', key: '2024-01-01'}]
 *
 * @example
 * // Quoted key with special characters
 * parsePartitionSelection('"my,key"')
 * // => [{type: 'single', key: 'my,key'}]
 *
 * @example
 * // Range
 * parsePartitionSelection('[2024-01-01...2024-12-31]')
 * // => [{type: 'range', start: '2024-01-01', end: '2024-12-31'}]
 *
 * @example
 * // Wildcard
 * parsePartitionSelection('2024-*')
 * // => [{type: 'wildcard', prefix: '2024-', suffix: ''}]
 *
 * @example
 * // Mixed list
 * parsePartitionSelection('key1, [2024-01-01...2024-01-31], 2024-*')
 * // => [
 * //   {type: 'single', key: 'key1'},
 * //   {type: 'range', start: '2024-01-01', end: '2024-01-31'},
 * //   {type: 'wildcard', prefix: '2024-', suffix: ''}
 * // ]
 */
export function parsePartitionSelection(text: string): ParsedPartitionTerm[] | Error {
  if (!text.trim()) {
    return [];
  }

  try {
    const lexer = new PartitionSelectionLexer(CharStream.fromString(text));

    const errorListener = new PartitionSelectionErrorListener();
    lexer.removeErrorListeners();
    lexer.addErrorListener(errorListener);

    const tokenStream = new CommonTokenStream(lexer);
    tokenStream.fill(); // Ensure all tokens are loaded before parsing

    const parser = new PartitionSelectionParser(tokenStream);

    parser.removeErrorListeners();
    parser.addErrorListener(errorListener);

    const tree = parser.start();

    const firstError = errorListener.errors[0];
    if (firstError) {
      return firstError;
    }

    const visitor = new AntlrPartitionSelectionVisitor();
    return visitor.visit(tree) ?? [];
  } catch (e) {
    return e instanceof Error ? e : new Error(String(e));
  }
}

// Re-export types for convenience
export type {ParsedPartitionTerm} from './AntlrPartitionSelectionVisitor';
