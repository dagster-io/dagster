import {BailErrorStrategy, CharStreams, CommonTokenStream} from 'antlr4ts';
import {ParseTree} from 'antlr4ts/tree/ParseTree';
import memoize from 'lodash/memoize';

import {CustomErrorListener, SyntaxError} from './CustomErrorListener';
import {SelectionAutoCompleteLexer} from './generated/SelectionAutoCompleteLexer';
import {SelectionAutoCompleteParser} from './generated/SelectionAutoCompleteParser';

/**
 * Represents the result of parsing, including the array of parse trees and any syntax errors.
 */
interface ParseResult {
  parseTrees: ParseTreeResult[];
  errors: SyntaxError[];
}

interface ParseTreeResult {
  tree: ParseTree;
  line: string;
}

/**
 * Parses the input and constructs an array of parse trees along with any syntax errors.
 * @param input - The input string to parse.
 * @returns The parse result containing the array of parse trees and syntax errors.
 */
export const parseInput = memoize((input: string): ParseResult => {
  const parseTrees: ParseTreeResult[] = [];
  const errors: SyntaxError[] = [];

  let currentPosition = 0;
  const inputLength = input.length;

  while (currentPosition < inputLength) {
    // Create a substring from the current position
    const substring = input.substring(currentPosition);

    // Initialize ANTLR input stream, lexer, and parser
    const inputStream = CharStreams.fromString(substring);
    const lexer = new SelectionAutoCompleteLexer(inputStream);
    const tokenStream = new CommonTokenStream(lexer);
    const parser = new SelectionAutoCompleteParser(tokenStream);

    // Attach custom error listener
    const errorListener = new CustomErrorListener();
    parser.removeErrorListeners();
    parser.addErrorListener(errorListener);

    // Set the error handler to bail on error to prevent infinite loops
    parser.errorHandler = new BailErrorStrategy();

    let tree: ParseTree | null = null;
    try {
      // Parse using the 'expr' rule instead of 'start' to allow partial parsing
      tree = parser.expr();
      parseTrees.push({tree, line: tree.text});

      // Advance currentPosition to the end of the parsed input
      const lastToken = tokenStream.get(tokenStream.index - 1);
      currentPosition += lastToken.stopIndex + 1;
    } catch {
      // Parsing error occurred
      const currentErrors = errorListener.getErrors();

      if (currentErrors.length > 0) {
        const error = currentErrors[0]!;
        const errorCharPos = error.column;
        const errorIndex = currentPosition + errorCharPos;

        // Parse up to the error
        const validInput = input.substring(currentPosition, errorIndex);
        if (validInput.trim().length > 0) {
          const validInputStream = CharStreams.fromString(validInput);
          const validLexer = new SelectionAutoCompleteLexer(validInputStream);
          const validTokenStream = new CommonTokenStream(validLexer);
          const validParser = new SelectionAutoCompleteParser(validTokenStream);

          // Remove error listeners for the valid parser
          validParser.removeErrorListeners();

          try {
            const validTree = validParser.expr();
            parseTrees.push({tree: validTree, line: validInput});
          } catch {
            // Ignore errors here since we already have an error in currentErrors
          }
        }

        // Add the error to the errors array
        errors.push({
          message: error.message,
          line: error.line,
          column: error.column + currentPosition,
          offendingSymbol: error.offendingSymbol,
        });

        // Advance currentPosition beyond the error
        currentPosition = errorIndex + 1;
      } else {
        // Critical parsing error, break the loop
        break;
      }
    }
  }

  return {parseTrees, errors};
});
