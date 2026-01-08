import {ParserRuleContext, TerminalNode} from 'antlr4ng';

import {BaseSelectionVisitor} from './BaseSelectionVisitor';
import {SelectionAutoCompleteProvider, Suggestion} from './SelectionAutoCompleteProvider';
import {
  getValueNodeValue,
  isInsideExpressionlessParenthesizedExpression,
  removeQuotesFromString,
} from './SelectionInputUtil';
import {
  AllExpressionContext,
  AndTokenContext,
  AttributeExpressionContext,
  AttributeNameContext,
  AttributeValueContext,
  ColonTokenContext,
  DownTraversalContext,
  FunctionNameContext,
  IncompleteAttributeExpressionMissingValueContext,
  IncompletePlusTraversalExpressionContext,
  IncompletePlusTraversalExpressionMissingValueContext,
  LeftParenTokenContext,
  OrTokenContext,
  PostDigitsWhitespaceContext,
  PostDownwardTraversalWhitespaceContext,
  PostLogicalOperatorWhitespaceContext,
  PostNeighborTraversalWhitespaceContext,
  PostNotOperatorWhitespaceContext,
  PostUpwardTraversalWhitespaceContext,
  UnmatchedValueContext,
  UpTraversalContext,
} from './generated/SelectionAutoCompleteParser';

const DEFAULT_TEXT_CALLBACK = (value: string) => value;

const DEBUG = false;

export class SelectionAutoCompleteVisitor extends BaseSelectionVisitor {
  private getAttributeResultsMatchingQuery: SelectionAutoCompleteProvider['getAttributeResultsMatchingQuery'];
  private getAttributeValueResultsMatchingQuery: SelectionAutoCompleteProvider['getAttributeValueResultsMatchingQuery'];
  private getAllResults: SelectionAutoCompleteProvider['getAllResults'];
  private getFunctionResultsMatchingQuery: SelectionAutoCompleteProvider['getFunctionResultsMatchingQuery'];
  private getSubstringResultMatchingQuery: SelectionAutoCompleteProvider['getSubstringResultMatchingQuery'];
  private createOperatorSuggestion: SelectionAutoCompleteProvider['createOperatorSuggestion'];
  private supportsTraversal: SelectionAutoCompleteProvider['supportsTraversal'];

  public list: Array<Suggestion> = [];

  public _startReplacementIndex: number;
  public _stopReplacementIndex: number;

  constructor({
    line,
    cursorIndex,
    getAttributeResultsMatchingQuery,
    getAttributeValueResultsMatchingQuery,
    getFunctionResultsMatchingQuery,
    getSubstringResultMatchingQuery,
    getAllResults,
    createOperatorSuggestion,
    supportsTraversal,
  }: {
    line: string;
    cursorIndex: number;
    getAttributeResultsMatchingQuery: SelectionAutoCompleteProvider['getAttributeResultsMatchingQuery'];
    getAttributeValueResultsMatchingQuery: SelectionAutoCompleteProvider['getAttributeValueResultsMatchingQuery'];
    getAllResults: SelectionAutoCompleteProvider['getAllResults'];
    getFunctionResultsMatchingQuery: SelectionAutoCompleteProvider['getFunctionResultsMatchingQuery'];
    getSubstringResultMatchingQuery: SelectionAutoCompleteProvider['getSubstringResultMatchingQuery'];
    createOperatorSuggestion: SelectionAutoCompleteProvider['createOperatorSuggestion'];
    supportsTraversal: SelectionAutoCompleteProvider['supportsTraversal'];
  }) {
    super({line, cursorIndex});
    this.getAttributeResultsMatchingQuery = getAttributeResultsMatchingQuery;
    this.getAttributeValueResultsMatchingQuery = getAttributeValueResultsMatchingQuery;
    this.getFunctionResultsMatchingQuery = getFunctionResultsMatchingQuery;
    this.getSubstringResultMatchingQuery = getSubstringResultMatchingQuery;
    this.getAllResults = getAllResults;
    this.createOperatorSuggestion = createOperatorSuggestion;
    this._startReplacementIndex = cursorIndex;
    this._stopReplacementIndex = cursorIndex;
    this.supportsTraversal = supportsTraversal;
  }

  set startReplacementIndex(newValue: number) {
    if (DEBUG) {
      console.log('Autocomplete suggestions being set by stack:', new Error());
    }
    this._startReplacementIndex = newValue;
  }
  set stopReplacementIndex(newValue: number) {
    this._stopReplacementIndex = newValue;
  }
  get startReplacementIndex() {
    return this._startReplacementIndex;
  }
  get stopReplacementIndex() {
    return this._stopReplacementIndex;
  }

  /** If we want to do nothing extra when cursor is outside any node, override from base. */
  protected handleCursorOutsideAnyNode(): void {
    // If there's no expression at all, we treat it as "empty input", so we add unmatched value results
    this.addUnmatchedValueResults('');
    this._startReplacementIndex = this.cursorIndex;
    this._stopReplacementIndex = this.cursorIndex;
  }

  public visitAllExpression(ctx: AllExpressionContext) {
    if (this.nodeIncludesCursor(ctx.postExpressionWhitespace())) {
      this.addAfterExpressionResults(ctx, {excludePlus: true});
    } else {
      this.startReplacementIndex = this.cursorIndex;
      this.stopReplacementIndex = this.cursorIndex;
      this.addUnmatchedValueResults('', DEFAULT_TEXT_CALLBACK, {excludePlus: true});
      if (isInsideExpressionlessParenthesizedExpression(ctx)) {
        this.list.push(
          this.createOperatorSuggestion({
            text: ')',
            type: 'parenthesis',
            displayText: ')',
          }),
        );
      }
    }
  }

  public visitUpTraversal(_ctx: UpTraversalContext) {
    this.list.push(
      this.createOperatorSuggestion({
        text: '()',
        type: 'parenthesis',
        displayText: '(',
      }),
    );
  }

  public visitDownTraversal(ctx: DownTraversalContext) {
    this.list.push(
      this.createOperatorSuggestion({
        text: ' and ',
        type: 'and',
        displayText: 'and',
      }),
    );
    this.list.push(
      this.createOperatorSuggestion({
        text: ' or ',
        type: 'or',
        displayText: 'or',
      }),
    );
    if (isInsideExpressionlessParenthesizedExpression(ctx)) {
      this.list.push(
        this.createOperatorSuggestion({
          text: ')',
          type: 'parenthesis',
          displayText: ')',
        }),
      );
    }
  }

  public visitFunctionName(ctx: FunctionNameContext) {
    if (this.nodeIncludesCursor(ctx)) {
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      this.startReplacementIndex = ctx.start!.start;
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      this.stopReplacementIndex = ctx.stop!.stop + 1;
      this.addFunctionResults(ctx.getText());
    }
  }

  public visitTerminal(ctx: TerminalNode) {
    if (this.nodeIncludesCursor(ctx)) {
      if (ctx.getText() === '=') {
        const parent = ctx.parent;
        if (parent instanceof AttributeExpressionContext) {
          const attrValue = parent.attributeValue(1);
          if (attrValue) {
            this.forceVisitCtx.add(attrValue);
          }
        }
      }
    }
  }

  public visitAttributeValue(ctx: AttributeValueContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const stopIndex = ctx.stop!.stop;
    if (
      this.cursorIndex >= stopIndex &&
      this.line[this.cursorIndex - 1] === '"' &&
      this.line[this.cursorIndex] !== '"'
    ) {
      this.addAfterExpressionResults(ctx);
      return;
    }
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    this.startReplacementIndex = ctx.start!.start;
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    this.stopReplacementIndex = ctx.stop!.stop + 1;

    const parentContext = ctx.parent;
    if (parentContext instanceof AttributeExpressionContext) {
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      this.startReplacementIndex = parentContext.colonToken()!.start!.start + 1;
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      this.stopReplacementIndex = parentContext.postAttributeValueWhitespace()!.start!.start;
    }

    const parentChildren = ctx.parent?.children ?? [];
    if (parentChildren[0] instanceof AttributeNameContext) {
      const rawValue = getValueNodeValue(ctx.value());
      this.addAttributeValueResults(parentChildren[0].getText(), rawValue);
    }
  }

  public visitColonToken(ctx: ColonTokenContext) {
    if (this.nodeIncludesCursor(ctx)) {
      let attributeName: ParserRuleContext | null = null;
      let valueNode: ParserRuleContext | null = null;

      const parentChildren = ctx.parent?.children ?? [];
      if (parentChildren[0] instanceof AttributeNameContext) {
        attributeName = parentChildren[0] as ParserRuleContext;
      }
      if (parentChildren[1] instanceof AttributeValueContext) {
        valueNode = parentChildren[1] as ParserRuleContext;
      } else if (parentChildren[2] instanceof AttributeValueContext) {
        valueNode = parentChildren[2] as ParserRuleContext;
      }

      // If the cursor is after the attribute name but before the value, suggest attribute values.
      if (attributeName?.stop && this.cursorIndex >= attributeName.stop?.stop) {
        this.addAttributeValueResults(attributeName.getText(), valueNode?.getText() ?? '');
      } else {
        // Possibly user typed partial attribute name
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        this.startReplacementIndex = ctx.start!.start - 1;
        this.stopReplacementIndex = this.startReplacementIndex;
        if (attributeName) {
          this.addAttributeResults(attributeName.getText());
        }
      }
    }
  }

  public visitAttributeName(ctx: AttributeNameContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    this.startReplacementIndex = ctx.start!.start;
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    this.stopReplacementIndex = ctx.stop!.stop + 2;
    this.addAttributeResults(ctx.getText());
  }

  public visitOrToken(ctx: OrTokenContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    if (this.cursorIndex > ctx.stop!.stop) {
      // Let whitespace token handle
    } else {
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      this.startReplacementIndex = ctx.start!.start;
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      this.stopReplacementIndex = ctx.stop!.stop + 1;
      this.list.push(
        this.createOperatorSuggestion({text: 'or', type: 'or', displayText: 'or'}),
        this.createOperatorSuggestion({text: 'and', type: 'and', displayText: 'and'}),
      );
    }
  }

  public visitAndToken(ctx: AndTokenContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    if (this.cursorIndex > ctx.stop!.stop) {
      // Let whitespace token handle
    } else {
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      this.startReplacementIndex = ctx.start!.start;
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      this.stopReplacementIndex = ctx.stop!.stop + 1;
      this.list.push(
        this.createOperatorSuggestion({text: 'and', type: 'and', displayText: 'and'}),
        this.createOperatorSuggestion({text: 'or', type: 'or', displayText: 'or'}),
      );
    }
  }

  public visitUnmatchedValue(ctx: UnmatchedValueContext) {
    if (this.nodeIncludesCursor(ctx)) {
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      this.startReplacementIndex = ctx.start!.start;
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      this.stopReplacementIndex = ctx.stop!.stop + 1;
      this.addUnmatchedValueResults(ctx.getText());
    }
  }

  public visitIncompletePlusTraversalExpressionMissingValue(
    ctx: IncompletePlusTraversalExpressionMissingValueContext,
  ) {
    const valueCtx = ctx.value();
    if (!valueCtx) {
      return;
    }
    const value = getValueNodeValue(valueCtx);
    if (this.nodeIncludesCursor(valueCtx)) {
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      this.startReplacementIndex = valueCtx.start!.start;
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      this.stopReplacementIndex = valueCtx.stop!.stop + 1;
      this.addUnmatchedValueResults(value, DEFAULT_TEXT_CALLBACK, {
        excludePlus: true,
      });
      return;
    }
  }

  public visitIncompletePlusTraversalExpression(ctx: IncompletePlusTraversalExpressionContext) {
    const wsCtx = ctx.postNeighborTraversalWhitespace();
    if (wsCtx && this.nodeIncludesCursor(wsCtx) && wsCtx.getText().length) {
      this.visit(wsCtx);
      return;
    }
    this.addUnmatchedValueResults('', DEFAULT_TEXT_CALLBACK, {
      excludeNot: true,
      excludePlus: true,
    });
  }

  public visitIncompleteAttributeExpressionMissingValue(
    ctx: IncompleteAttributeExpressionMissingValueContext,
  ) {
    const attrNameCtx = ctx.attributeName();
    if (!attrNameCtx) {
      return;
    }
    if (this.nodeIncludesCursor(attrNameCtx)) {
      this.visit(attrNameCtx);
    } else {
      const wsCtx = ctx.attributeValueWhitespace();
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      this.startReplacementIndex = wsCtx!.start!.start;
      this.stopReplacementIndex = this.startReplacementIndex;
      this.addAttributeValueResults(attrNameCtx.getText(), '');
    }
  }

  public visitPostNotOperatorWhitespace(ctx: PostNotOperatorWhitespaceContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const needsWhitespace = this.cursorIndex === ctx.start!.start;
    this.addUnmatchedValueResults('', (value) => `${needsWhitespace ? ' ' : ''}${value}`, {
      excludeNot: true,
    });
  }

  public visitPostNeighborTraversalWhitespace(_ctx: PostNeighborTraversalWhitespaceContext) {
    this.addUnmatchedValueResults('', DEFAULT_TEXT_CALLBACK, {excludePlus: true});
  }

  public visitPostUpwardTraversalWhitespace(_ctx: PostUpwardTraversalWhitespaceContext) {
    this.addUnmatchedValueResults('', DEFAULT_TEXT_CALLBACK, {excludePlus: true});
  }

  public visitPostDownwardTraversalWhitespace(ctx: PostDownwardTraversalWhitespaceContext) {
    this.addAfterExpressionResults(ctx, {excludePlus: true});
  }

  public visitPostExpressionWhitespace(ctx: ParserRuleContext) {
    if (!this.list.length) {
      this.addAfterExpressionResults(ctx);
    }
  }

  public visitPostDigitsWhitespace(ctx: PostDigitsWhitespaceContext) {
    if (!this.supportsTraversal) {
      return;
    }
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    this.startReplacementIndex = ctx.start!.start;
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    this.stopReplacementIndex = ctx.stop!.stop;
    this.list.push(
      this.createOperatorSuggestion({
        text: '+',
        type: 'up-traversal',
        displayText: '+',
      }),
    );
  }

  public visitPostLogicalOperatorWhitespace(ctx: PostLogicalOperatorWhitespaceContext) {
    if (!this.list.length) {
      const isAfterNot = this.line.slice(0, this.cursorIndex).trim().toLowerCase().endsWith('not');
      const isAfterLeftParen = this.line[this.cursorIndex - 1] === '(';
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const needsWhitespace = !isAfterLeftParen && this.cursorIndex === ctx.start!.start;
      this.addUnmatchedValueResults('', (text) => `${needsWhitespace ? ' ' : ''}${text}`, {
        excludeNot: isAfterNot,
      });
    }
  }

  public visitLeftParenToken(_ctx: LeftParenTokenContext) {
    this.addUnmatchedValueResults('');
  }

  private addAttributeResults(
    value: string,
    textCallback: (value: string) => string = DEFAULT_TEXT_CALLBACK,
  ) {
    this.list.push(
      ...this.getAttributeResultsMatchingQuery({
        query: value.trim(),
        textCallback,
      }),
    );
  }

  private addFunctionResults(
    value: string,
    textCallback: (value: string) => string = DEFAULT_TEXT_CALLBACK,
    includeParenthesis: boolean = false,
  ) {
    this.list.push(
      ...this.getFunctionResultsMatchingQuery({
        query: value.trim(),
        textCallback,
        options: {includeParenthesis},
      }),
    );
  }

  public addUnmatchedValueResults(
    _value: string,
    textCallback: (value: string) => string = DEFAULT_TEXT_CALLBACK,
    options: {excludeNot?: boolean; excludePlus?: boolean} = {},
  ) {
    const value = _value.trim();
    if (value) {
      this.list.push(
        this.getSubstringResultMatchingQuery({
          query: value,
          textCallback,
        }),
      );
    }
    this.addAttributeResults(value, textCallback);
    this.addFunctionResults(value, textCallback, true);

    if (value) {
      this.list.push(
        ...this.getAllResults({
          query: value,
          textCallback,
        }),
      );
    }

    if (!options.excludeNot && 'not'.startsWith(value)) {
      this.list.push(
        this.createOperatorSuggestion({
          text: textCallback('not '),
          type: 'not',
          displayText: 'not',
        }),
      );
    }
    if (value === '') {
      if (!options.excludePlus && this.supportsTraversal) {
        this.list.push(
          this.createOperatorSuggestion({
            text: textCallback('+'),
            type: 'up-traversal',
            displayText: '+',
          }),
        );
      }
      this.list.push(
        this.createOperatorSuggestion({
          text: textCallback('()'),
          type: 'parenthesis',
          displayText: '(',
        }),
      );
    }
  }

  private addAttributeValueResults(
    attributeKey: string,
    value: string,
    textCallback: (value: string) => string = DEFAULT_TEXT_CALLBACK,
  ) {
    const unquotedValue = removeQuotesFromString(value);
    this.list.push(
      ...this.getAttributeValueResultsMatchingQuery({
        attribute: attributeKey,
        query: unquotedValue,
        textCallback,
      }),
    );
  }

  private addAfterExpressionResults(
    ctx: ParserRuleContext,
    options: {
      excludePlus?: boolean;
    } = {},
  ) {
    this.list.push(
      this.createOperatorSuggestion({text: ' and ', type: 'and', displayText: 'and'}),
      this.createOperatorSuggestion({text: ' or ', type: 'or', displayText: 'or'}),
    );

    if (!options.excludePlus && this.supportsTraversal) {
      this.list.push(
        this.createOperatorSuggestion({text: '+', type: 'down-traversal', displayText: '+'}),
      );
    }

    if (isInsideExpressionlessParenthesizedExpression(ctx)) {
      this.list.push(
        this.createOperatorSuggestion({text: ')', type: 'parenthesis', displayText: ')'}),
      );
    }
  }
}
