import {ParserRuleContext} from 'antlr4ts';
import {TerminalNode} from 'antlr4ts/tree/TerminalNode';

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
  private getAttributeValueIncludeAttributeResultsMatchingQuery: SelectionAutoCompleteProvider['getAttributeValueIncludeAttributeResultsMatchingQuery'];
  private getFunctionResultsMatchingQuery: SelectionAutoCompleteProvider['getFunctionResultsMatchingQuery'];
  private getSubstringResultMatchingQuery: SelectionAutoCompleteProvider['getSubstringResultMatchingQuery'];
  private createOperatorSuggestion: SelectionAutoCompleteProvider['createOperatorSuggestion'];

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
    getAttributeValueIncludeAttributeResultsMatchingQuery,
    createOperatorSuggestion,
  }: {
    line: string;
    cursorIndex: number;
    getAttributeResultsMatchingQuery: SelectionAutoCompleteProvider['getAttributeResultsMatchingQuery'];
    getAttributeValueResultsMatchingQuery: SelectionAutoCompleteProvider['getAttributeValueResultsMatchingQuery'];
    getAttributeValueIncludeAttributeResultsMatchingQuery: SelectionAutoCompleteProvider['getAttributeValueIncludeAttributeResultsMatchingQuery'];
    getFunctionResultsMatchingQuery: SelectionAutoCompleteProvider['getFunctionResultsMatchingQuery'];
    getSubstringResultMatchingQuery: SelectionAutoCompleteProvider['getSubstringResultMatchingQuery'];
    createOperatorSuggestion: SelectionAutoCompleteProvider['createOperatorSuggestion'];
  }) {
    super({line, cursorIndex});
    this.getAttributeResultsMatchingQuery = getAttributeResultsMatchingQuery;
    this.getAttributeValueResultsMatchingQuery = getAttributeValueResultsMatchingQuery;
    this.getFunctionResultsMatchingQuery = getFunctionResultsMatchingQuery;
    this.getSubstringResultMatchingQuery = getSubstringResultMatchingQuery;
    this.getAttributeValueIncludeAttributeResultsMatchingQuery =
      getAttributeValueIncludeAttributeResultsMatchingQuery;
    this.createOperatorSuggestion = createOperatorSuggestion;
    this._startReplacementIndex = cursorIndex;
    this._stopReplacementIndex = cursorIndex;
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
      this.startReplacementIndex = ctx.start.startIndex;
      this.stopReplacementIndex = ctx.stop!.stopIndex + 1;
      this.addFunctionResults(ctx.text);
    }
  }

  public visitTerminal(ctx: TerminalNode) {
    if (this.nodeIncludesCursor(ctx)) {
      if (ctx.text === '=') {
        const parent = ctx.parent;
        if (parent instanceof AttributeExpressionContext) {
          this.forceVisitCtx.add(parent.attributeValue(1));
        }
      }
    }
  }

  public visitAttributeValue(ctx: AttributeValueContext) {
    const stopIndex = ctx.stop!.stopIndex;
    if (
      this.cursorIndex >= stopIndex &&
      this.line[this.cursorIndex - 1] === '"' &&
      this.line[this.cursorIndex] !== '"'
    ) {
      this.addAfterExpressionResults(ctx);
      return;
    }
    this.startReplacementIndex = ctx.start!.startIndex;
    this.stopReplacementIndex = ctx.stop!.stopIndex + 1;

    const parentContext = ctx.parent;
    if (parentContext instanceof AttributeExpressionContext) {
      this.startReplacementIndex = parentContext.colonToken().start.startIndex + 1;
      this.stopReplacementIndex = parentContext.postAttributeValueWhitespace().start!.startIndex;
    }

    const parentChildren = ctx.parent?.children ?? [];
    if (parentChildren[0] instanceof AttributeNameContext) {
      const rawValue = getValueNodeValue(ctx.value());
      this.addAttributeValueResults(parentChildren[0].text, rawValue);
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
      if (attributeName?.stop && this.cursorIndex >= attributeName.stop?.stopIndex) {
        this.addAttributeValueResults(attributeName.text, valueNode?.text ?? '');
      } else {
        // Possibly user typed partial attribute name
        this.startReplacementIndex = ctx.start.startIndex - 1;
        this.stopReplacementIndex = this.startReplacementIndex;
        if (attributeName) {
          this.addAttributeResults(attributeName.text);
        }
      }
    }
  }

  public visitAttributeName(ctx: AttributeNameContext) {
    this.startReplacementIndex = ctx.start.startIndex;
    this.stopReplacementIndex = ctx.stop!.stopIndex + 2;
    this.addAttributeResults(ctx.text);
  }

  public visitOrToken(ctx: OrTokenContext) {
    if (this.cursorIndex > ctx.stop!.stopIndex) {
      // Let whitespace token handle
    } else {
      this.startReplacementIndex = ctx.start.startIndex;
      this.stopReplacementIndex = ctx.stop!.stopIndex + 1;
      this.list.push(
        this.createOperatorSuggestion({text: 'or', type: 'or', displayText: 'or'}),
        this.createOperatorSuggestion({text: 'and', type: 'and', displayText: 'and'}),
      );
    }
  }

  public visitAndToken(ctx: AndTokenContext) {
    if (this.cursorIndex > ctx.stop!.stopIndex) {
      // Let whitespace token handle
    } else {
      this.startReplacementIndex = ctx.start.startIndex;
      this.stopReplacementIndex = ctx.stop!.stopIndex + 1;
      this.list.push(
        this.createOperatorSuggestion({text: 'and', type: 'and', displayText: 'and'}),
        this.createOperatorSuggestion({text: 'or', type: 'or', displayText: 'or'}),
      );
    }
  }

  public visitUnmatchedValue(ctx: UnmatchedValueContext) {
    if (this.nodeIncludesCursor(ctx)) {
      this.startReplacementIndex = ctx.start.startIndex;
      this.stopReplacementIndex = ctx.stop!.stopIndex + 1;
      this.addUnmatchedValueResults(ctx.text);
    }
  }

  public visitIncompletePlusTraversalExpressionMissingValue(
    ctx: IncompletePlusTraversalExpressionMissingValueContext,
  ) {
    const value = getValueNodeValue(ctx.value());
    if (this.nodeIncludesCursor(ctx.value())) {
      this.startReplacementIndex = ctx.value().start.startIndex;
      this.stopReplacementIndex = ctx.value().stop!.stopIndex + 1;
      this.addUnmatchedValueResults(value, DEFAULT_TEXT_CALLBACK, {
        excludePlus: true,
      });
      return;
    }
  }

  public visitIncompletePlusTraversalExpression(ctx: IncompletePlusTraversalExpressionContext) {
    if (
      this.nodeIncludesCursor(ctx.postNeighborTraversalWhitespace()) &&
      ctx.postNeighborTraversalWhitespace().text.length
    ) {
      this.visit(ctx.postNeighborTraversalWhitespace());
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
    if (this.nodeIncludesCursor(ctx.attributeName())) {
      this.visit(ctx.attributeName());
    } else {
      this.startReplacementIndex = ctx.attributeValueWhitespace().start.startIndex;
      this.stopReplacementIndex = this.startReplacementIndex;
      this.addAttributeValueResults(ctx.attributeName().text, '');
    }
  }

  public visitPostNotOperatorWhitespace(ctx: PostNotOperatorWhitespaceContext) {
    const needsWhitespace = this.cursorIndex === ctx.start.startIndex;
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
    this.startReplacementIndex = ctx.start.startIndex;
    this.stopReplacementIndex = ctx.stop!.stopIndex;
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
      const needsWhitespace = !isAfterLeftParen && this.cursorIndex === ctx.start.startIndex;
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
        ...this.getAttributeValueIncludeAttributeResultsMatchingQuery({
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
      if (!options.excludePlus) {
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

    if (!options.excludePlus) {
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
