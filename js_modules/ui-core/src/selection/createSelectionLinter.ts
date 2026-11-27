import {
  AbstractParseTreeVisitor,
  BaseErrorListener,
  CommonTokenStream,
  Lexer,
  Parser,
  ParserRuleContext,
} from 'antlr4ng';

import {CustomErrorListener, SyntaxError} from './CustomErrorListener';
import {getLeadingWhitespaceLength, parseInput} from './SelectionInputParser';
import {Utf16CharStream} from './Utf16CharStream';
import {weakMapMemoize} from '../util/weakMapMemoize';
import {AttributeNameContext} from './generated/SelectionAutoCompleteParser';
import {SelectionAutoCompleteVisitor} from './generated/SelectionAutoCompleteVisitor';

type LexerConstructor = new (...args: ConstructorParameters<typeof Lexer>) => Lexer;
type ParserConstructor = new (...args: ConstructorParameters<typeof Parser>) => Parser & {
  start: () => ParserRuleContext;
};

export function createSelectionLinter({
  Lexer: LexerKlass,
  Parser: ParserKlass,
  supportedAttributes,
  unsupportedAttributeMessages = {},
}: {
  Lexer: LexerConstructor;
  Parser: ParserConstructor;
  supportedAttributes: readonly string[];
  unsupportedAttributeMessages?: Record<string, string>;
}) {
  const linter = (text: string) => {
    if (!text.length) {
      return [];
    }

    // Lex from after the leading whitespace, keeping offsets relative to the whole text. The error
    // listener reports columns, so the lexer's column starts there too.
    const start = getLeadingWhitespaceLength(text);
    const inputStream = new Utf16CharStream(text);
    inputStream.seek(start);
    const lexer = new LexerKlass(inputStream);
    lexer.column = start;

    const lexerErrorListener = new CustomErrorListener();
    const lexerErrorStarts = new LexerErrorStartListener(lexer);
    lexer.removeErrorListeners();
    lexer.addErrorListener(lexerErrorListener);
    lexer.addErrorListener(lexerErrorStarts);

    const tokens = new CommonTokenStream(lexer);
    tokens.fill(); // Ensure all tokens are loaded before parsing

    const parser = new ParserKlass(tokens);

    const errorListener = new CustomErrorListener();

    parser.removeErrorListeners(); // Remove default console error listener
    parser.addErrorListener(errorListener);

    parser.start();

    const lexerErrors = mergeSurrogatePairErrors(
      text,
      lexerErrorListener.getErrors(),
      lexerErrorStarts.starts,
    );

    // Map syntax errors to CodeMirror's lint format
    const lintErrors = [...lexerErrors, ...errorListener.getErrors()].map((error) => ({
      ...error,
      message: error.message.replace('<EOF>, ', ''),
    }));

    const {parseTrees} = parseInput(text);
    const attributeVisitor = new InvalidAttributeVisitor(
      supportedAttributes,
      unsupportedAttributeMessages,
      lintErrors,
    );
    parseTrees.forEach(({tree, startOffset}) => {
      attributeVisitor.treeOffset = startOffset;
      tree.accept(attributeVisitor);
    });

    return lintErrors.concat(attributeVisitor.getErrors());
  };
  return weakMapMemoize(linter, {maxEntries: 20});
}

// Records where each lexer error starts in the whole text; the error's `from` is a column.
class LexerErrorStartListener extends BaseErrorListener {
  starts: number[] = [];

  constructor(private lexer: Lexer) {
    super();
  }

  override syntaxError() {
    this.starts.push(this.lexer.tokenStartCharIndex);
  }
}

const isSurrogatePairAt = (text: string, index: number) => {
  const high = text.charCodeAt(index);
  const low = text.charCodeAt(index + 1);
  return high >= 0xd800 && high <= 0xdbff && low >= 0xdc00 && low <= 0xdfff;
};

/**
 * The lexer reads UTF-16 code units, so it rejects a character above U+FFFF (an emoji) as two
 * errors. Merge each such pair into one error that names the whole character.
 */
const mergeSurrogatePairErrors = (text: string, errors: SyntaxError[], starts: number[]) =>
  errors.flatMap((error, index) => {
    const start = starts[index];
    const previousStart = starts[index - 1];
    const nextStart = starts[index + 1];
    if (start === undefined) {
      return [error];
    }
    if (previousStart === start - 1 && isSurrogatePairAt(text, previousStart)) {
      return [];
    }
    if (nextStart === start + 1 && isSurrogatePairAt(text, start)) {
      const character = text.slice(start, start + 2);
      return [{...error, message: `token recognition error at: '${character}'`}];
    }
    return [error];
  });

class InvalidAttributeVisitor
  extends AbstractParseTreeVisitor<void>
  implements SelectionAutoCompleteVisitor<void>
{
  private errors: SyntaxError[] = [];
  private sortedLintErrors: SyntaxError[];
  /** Start of the current parse tree in the full text; tree token offsets are local to it. */
  treeOffset = 0;

  constructor(
    private supportedAttributes: readonly string[],
    private unsupportedAttributeMessages: Record<string, string>,
    lintErrors: SyntaxError[],
  ) {
    super();
    // Sort errors by start position for efficient searching
    this.sortedLintErrors = [...lintErrors].sort((a, b) => a.from - b.from);
  }

  getErrors() {
    return this.errors;
  }

  defaultResult() {
    return undefined;
  }

  private hasOverlap(from: number, to: number): boolean {
    // Binary search to find the first error that could potentially overlap
    let low = 0;
    let high = this.sortedLintErrors.length - 1;

    while (low <= high) {
      const mid = Math.floor((low + high) / 2);
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const error = this.sortedLintErrors[mid]!;

      if (error.to < from) {
        low = mid + 1;
      } else if (error.from > to) {
        high = mid - 1;
      } else {
        // Found an overlapping error
        return true;
      }
    }
    return false;
  }

  visitAttributeName(ctx: AttributeNameContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const attributeName = ctx.IDENTIFIER()!.getText();
    const {start, stop} = ctx;
    if (!this.supportedAttributes.includes(attributeName) && start && stop) {
      const from = start.start + this.treeOffset;
      const to = stop.stop + 1 + this.treeOffset;

      if (!this.hasOverlap(from, to)) {
        this.errors.push({
          message:
            this.unsupportedAttributeMessages[attributeName] ??
            `Unsupported attribute: "${attributeName}"`,
          from,
          to,
        });
      }
    }
  }
}
