import {CharStreams, CommonTokenStream, Lexer, Parser, ParserRuleContext} from 'antlr4ts';
import {AbstractParseTreeVisitor} from 'antlr4ts/tree/AbstractParseTreeVisitor';

import {CustomErrorListener, SyntaxError} from './CustomErrorListener';
import {parseInput} from './SelectionInputParser';
import {weakMapMemoize} from '../util/weakMapMemoize';
import {AttributeNameContext} from './generated/SelectionAutoCompleteParser';
import {SelectionAutoCompleteVisitor} from './generated/SelectionAutoCompleteVisitor';

type LexerConstructor = new (...args: any[]) => Lexer;
type ParserConstructor = new (...args: any[]) => Parser & {
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

    const inputStream = CharStreams.fromString(text);
    const lexer = new LexerKlass(inputStream);

    const tokens = new CommonTokenStream(lexer);
    const parser = new ParserKlass(tokens);

    const errorListener = new CustomErrorListener();

    lexer.removeErrorListeners();
    lexer.addErrorListener(errorListener);

    parser.removeErrorListeners(); // Remove default console error listener
    parser.addErrorListener(errorListener);

    parser.start();

    // Map syntax errors to CodeMirror's lint format
    const lintErrors = errorListener.getErrors().map((error) => ({
      ...error,
      message: error.message.replace('<EOF>, ', ''),
    }));

    const {parseTrees} = parseInput(text);
    const attributeVisitor = new InvalidAttributeVisitor(
      supportedAttributes,
      unsupportedAttributeMessages,
      lintErrors,
    );
    parseTrees.forEach(({tree}) => tree.accept(attributeVisitor));

    return lintErrors.concat(attributeVisitor.getErrors());
  };
  return weakMapMemoize(linter, {maxEntries: 20});
}

class InvalidAttributeVisitor
  extends AbstractParseTreeVisitor<void>
  implements SelectionAutoCompleteVisitor<void>
{
  private errors: SyntaxError[] = [];
  private sortedLintErrors: SyntaxError[];

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
    const attributeName = ctx.IDENTIFIER().text;
    if (!this.supportedAttributes.includes(attributeName)) {
      const from = ctx.start.startIndex;
      const to = ctx.stop!.stopIndex + 1;

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
