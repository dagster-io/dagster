import {CharStreams, CommonTokenStream, ParserRuleContext} from 'antlr4ts';

import {BaseSelectionVisitor} from '../BaseSelectionVisitor';
import {SelectionAutoCompleteLexer} from '../generated/SelectionAutoCompleteLexer';
import {
  AttributeValueContext,
  SelectionAutoCompleteParser,
  UnmatchedValueContext,
} from '../generated/SelectionAutoCompleteParser';

class TestBaseVisitor extends BaseSelectionVisitor {
  public visitedNodes: string[] = [];

  protected handleCursorOutsideAnyNode(): void {
    this.visitedNodes.push('handleCursorOutsideAnyNode');
  }

  public visitUnmatchedValue(ctx: UnmatchedValueContext) {
    this.visitedNodes.push(
      `visitUnmatchedValue: [${ctx.start.startIndex}, ${ctx.stop?.stopIndex}]`,
    );
  }

  public visitAttributeName(ctx: ParserRuleContext) {
    this.visitedNodes.push(`visitAttributeName: [${ctx.start.startIndex}, ${ctx.stop?.stopIndex}]`);
  }

  public visitAttributeValue(ctx: AttributeValueContext) {
    this.visitedNodes.push(
      `visitAttributeValue: [${ctx.start.startIndex}, ${ctx.stop?.stopIndex}]`,
    );
  }
}

/**
 * Helper function to parse input and return the root context.
 */
function parseInput(line: string) {
  const inputStream = CharStreams.fromString(line);
  const lexer = new SelectionAutoCompleteLexer(inputStream);
  const tokenStream = new CommonTokenStream(lexer);
  const parser = new SelectionAutoCompleteParser(tokenStream);
  parser.removeErrorListeners(); // Remove default error listeners
  const errorListener = {
    syntaxError: (
      _recog: any,
      _offendingSymbol: any,
      _line: number,
      _charPositionInLine: number,
      _msg: string,
      _e: any,
    ) => {},
  };
  parser.addErrorListener(errorListener);
  const tree = parser.start();
  return tree;
}

describe('BaseSelectionVisitor with Real Contexts', () => {
  it('skips node when the cursor is not in range', () => {
    const input = 'key:"value"';
    const cursorIndex = 15; // Position outside the range
    const tree = parseInput(input);

    const visitor = new TestBaseVisitor({line: input, cursorIndex});
    visitor.visit(tree);

    expect(visitor.visitedNodes).toEqual(['handleCursorOutsideAnyNode']);
  });

  it('visits node when the cursor is in range', () => {
    const input = 'key:"value"';
    const cursorIndex = 5; // Position within the key attribute
    const tree = parseInput(input);

    const visitor = new TestBaseVisitor({line: input, cursorIndex});
    visitor.visit(tree);

    expect(visitor.visitedNodes).toContain('visitAttributeValue: [4, 10]');
  });

  it('forces visiting a node with forceVisit even if cursor not in range', () => {
    const input = 'key:"value"';
    const cursorIndex = 15; // Position outside the range
    const tree = parseInput(input);

    const visitor = new TestBaseVisitor({line: input, cursorIndex});
    visitor.visit(tree); // Out-of-range visit
    expect(visitor.visitedNodes).toEqual(['handleCursorOutsideAnyNode']);
  });

  it('handles nested expressions correctly', () => {
    const input = '(key:"value" and tag:"value2" or owner:"owner1")+';
    const cursorIndex = 25; // Position within the 'value2' attribute value
    const tree = parseInput(input);

    const visitor = new TestBaseVisitor({line: input, cursorIndex});
    visitor.visit(tree);

    expect(visitor.visitedNodes).toEqual(['visitAttributeValue: [21, 28]']);
  });

  it('handles cursor at the end of the input', () => {
    const input = 'key:"value"';
    const cursorIndex = input.length; // Position right after the last character
    const tree = parseInput(input);

    const visitor = new TestBaseVisitor({line: input, cursorIndex});
    visitor.visit(tree);

    expect(visitor.visitedNodes).toEqual(['visitAttributeValue: [4, 10]']);
  });
});
