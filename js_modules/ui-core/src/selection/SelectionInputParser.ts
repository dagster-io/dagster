import {BailErrorStrategy, CommonTokenStream, ParseTree, ParserRuleContext} from 'antlr4ng';
import memoize from 'lodash/memoize';

import {CustomErrorListener, SyntaxError} from './CustomErrorListener';
import {Utf16CharStream} from './Utf16CharStream';
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
  /**
   * Start of the tree in the input. `line` can be shorter than the text it covers, because the
   * lexer drops characters it rejects.
   */
  startOffset: number;
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
    const inputStream = new Utf16CharStream(substring);
    const lexer = new SelectionAutoCompleteLexer(inputStream);
    lexer.removeErrorListeners();
    const tokenStream = new CommonTokenStream(lexer);
    tokenStream.fill(); // Ensure all tokens are loaded before parsing

    const parser = new SelectionAutoCompleteParser(tokenStream);

    // Attach custom error listener
    const errorListener = new CustomErrorListener();
    parser.removeErrorListeners();

    // Set the error handler to bail on error to prevent infinite loops
    parser.errorHandler = new BailErrorStrategy();

    let tree: ParseTree | null = null;
    try {
      // Parse using the 'expr' rule instead of 'start' to allow partial parsing
      tree = parser.expr();

      parseTrees.push({
        tree,
        line: (tree as ParserRuleContext).getText(),
        startOffset: currentPosition,
      });

      // Advance currentPosition to the end of the parsed input
      const lastToken = tokenStream.get(tokenStream.index - 1);
      currentPosition += lastToken.stop + 1;
    } catch {
      // Parsing error occurred
      const currentErrors = errorListener.getErrors();

      if (currentErrors.length > 0) {
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        const error = currentErrors[0]!;
        const errorCharPos = error.from;
        const errorIndex = currentPosition + errorCharPos;

        // Parse up to the error
        const validInput = input.substring(currentPosition, errorIndex);
        if (validInput.trim().length > 0) {
          const validInputStream = new Utf16CharStream(validInput);
          const validLexer = new SelectionAutoCompleteLexer(validInputStream);
          validLexer.removeErrorListeners();
          const validTokenStream = new CommonTokenStream(validLexer);
          validTokenStream.fill(); // Ensure all tokens are loaded before parsing

          const validParser = new SelectionAutoCompleteParser(validTokenStream);

          // Remove error listeners for the valid parser
          validParser.removeErrorListeners();

          try {
            const validTree = validParser.expr();
            parseTrees.push({tree: validTree, line: validInput, startOffset: currentPosition});
          } catch {
            // Ignore errors here since we already have an error in currentErrors
          }
        }

        // Add the error to the errors array
        errors.push({
          message: error.message,
          from: error.from + currentPosition,
          to: error.to + currentPosition,
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
