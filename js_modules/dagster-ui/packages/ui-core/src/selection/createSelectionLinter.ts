import {CharStreams, CommonTokenStream, Lexer, Parser, ParserRuleContext} from 'antlr4ts';
import {AbstractParseTreeVisitor} from 'antlr4ts/tree/AbstractParseTreeVisitor';
import CodeMirror from 'codemirror';

import {CustomErrorListener} from './CustomErrorListener';
import {parseInput} from './SelectionInputParser';
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
  return (text: string) => {
    if (!text.length) {
      return [];
    }
    const errorListener = new CustomErrorListener();

    const inputStream = CharStreams.fromString(text);
    const lexer = new LexerKlass(inputStream);

    lexer.removeErrorListeners();
    lexer.addErrorListener(errorListener);

    const tokens = new CommonTokenStream(lexer);
    const parser = new ParserKlass(tokens);

    parser.removeErrorListeners(); // Remove default console error listener
    parser.addErrorListener(errorListener);

    parser.start();

    // Map syntax errors to CodeMirror's lint format
    const lintErrors = errorListener.getErrors().map((error) => ({
      message: error.message.replace('<EOF>, ', ''),
      severity: 'error',
      from: CodeMirror.Pos(0, error.column),
      to: CodeMirror.Pos(0, text.length),
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
}

class InvalidAttributeVisitor
  extends AbstractParseTreeVisitor<void>
  implements SelectionAutoCompleteVisitor<void>
{
  private errors: {
    message: string;
    severity: 'error' | 'warning';
    from: CodeMirror.Position;
    to: CodeMirror.Position;
  }[] = [];
  private sortedLintErrors: {from: CodeMirror.Position; to: CodeMirror.Position}[];

  constructor(
    private supportedAttributes: readonly string[],
    private unsupportedAttributeMessages: Record<string, string>,
    lintErrors: {from: CodeMirror.Position; to: CodeMirror.Position}[],
  ) {
    super();
    // Sort errors by start position for efficient searching
    this.sortedLintErrors = [...lintErrors].sort((a, b) => a.from.ch - b.from.ch);
  }

  getErrors() {
    return this.errors;
  }

  defaultResult() {
    return undefined;
  }

  private hasOverlap(from: CodeMirror.Position, to: CodeMirror.Position): boolean {
    // Binary search to find the first error that could potentially overlap
    let low = 0;
    let high = this.sortedLintErrors.length - 1;

    while (low <= high) {
      const mid = Math.floor((low + high) / 2);
      const error = this.sortedLintErrors[mid]!;

      if (error.to.ch < from.ch) {
        low = mid + 1;
      } else if (error.from.ch > to.ch) {
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
      const from = CodeMirror.Pos(0, ctx.start.startIndex);
      const to = CodeMirror.Pos(0, ctx.stop!.stopIndex + 1);

      if (!this.hasOverlap(from, to)) {
        this.errors.push({
          message:
            this.unsupportedAttributeMessages[attributeName] ??
            `Unsupported attribute: ${attributeName}`,
          severity: 'error',
          from,
          to,
        });
      }
    }
  }
}
