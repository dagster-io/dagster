import {ParserRuleContext, TerminalNode} from 'antlr4ng';

import {BaseSelectionVisitor} from './BaseSelectionVisitor';
import {
  QuotedValue,
  SelectionAutoCompleteProvider,
  Suggestion,
} from './SelectionAutoCompleteProvider';
import {
  KEY_VALUE_ATTRIBUTES,
  getUnquotedValueProblem,
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
  IncompleteAttributeExpressionMissingSecondValueContext,
  IncompleteAttributeExpressionMissingValueContext,
  IncompleteLeftQuotedStringValueContext,
  IncompletePlusTraversalExpressionContext,
  IncompletePlusTraversalExpressionMissingValueContext,
  IncompleteRightQuotedStringValueContext,
  LeftParenTokenContext,
  NullStringValueContext,
  OrTokenContext,
  PostDigitsWhitespaceContext,
  PostDownwardTraversalWhitespaceContext,
  PostLogicalOperatorWhitespaceContext,
  PostNeighborTraversalWhitespaceContext,
  PostNotOperatorWhitespaceContext,
  PostUpwardTraversalWhitespaceContext,
  QuotedStringValueContext,
  UnmatchedValueContext,
  UnquotedRejectedValueContext,
  UpTraversalContext,
} from './generated/SelectionAutoCompleteParser';

const DEFAULT_TEXT_CALLBACK = (value: string) => value;

const DEBUG = false;

/** What may follow a value that ends where it was typed: whitespace, `)`, or nothing. */
const VALUE_END_PATTERN = /^(?:[ \t\r\n)]|$)/;

/** On pages with traversal, a complete downstream layer (`+` or `+2`) can also follow a value. */
const TRAVERSAL_VALUE_END_PATTERN = /^(?:\+[0-9]*)?(?:[ \t\r\n)]|$)/;

type AttributeValueResultsOptions = {
  quotedValue?: QuotedValue;
  key?: string;
};

/**
 * The expression's value with quotes added, when the shared grammar rejects part of it unquoted
 * and quoting can fix it.
 */
function getQuotedValue(
  ctx: AttributeExpressionContext,
  supportsTraversal: boolean | undefined,
): QuotedValue | undefined {
  const values = ctx.attributeValue().map((attributeValue) => attributeValue.value());
  const problems = values
    .filter((value) => value instanceof UnquotedRejectedValueContext)
    .map((value) => getUnquotedValueProblem(value.getText()));
  if (!problems.length) {
    return undefined;
  }

  // A backslash can't be escaped yet and a hidden character should be removed, so quoting isn't
  // offered for unquoted values with either.
  if (
    problems.some(
      (problem) => problem?.type === 'hidden-character' || problem?.type === 'backslash',
    )
  ) {
    return undefined;
  }

  // With an incomplete quote the parser can't tell where the value ends, so quoting could cut it short.
  if (
    values.some(
      (value) =>
        value instanceof IncompleteLeftQuotedStringValueContext ||
        value instanceof IncompleteRightQuotedStringValueContext,
    )
  ) {
    return undefined;
  }

  // The parser ends a value at characters like `+` and `:`, so when the typed text runs on past it,
  // quoting would wrap only the start of what was typed.
  const lastValueToken = ctx.attributeValue().at(-1)?.stop;
  const stream = lastValueToken?.inputStream;
  const rest = stream
    ? stream.getTextFromRange((lastValueToken?.stop ?? 0) + 1, stream.size - 1)
    : '';
  const valueEndPattern = supportsTraversal ? TRAVERSAL_VALUE_END_PATTERN : VALUE_END_PATTERN;
  if (!valueEndPattern.test(rest)) {
    return undefined;
  }

  // Only tag attributes take key=value, so quoting a pair on another attribute is still invalid.
  const attribute = ctx.attributeName().getText();
  if (values.length > 1 && !(KEY_VALUE_ATTRIBUTES as readonly string[]).includes(attribute)) {
    return undefined;
  }

  const text = values
    .map((value) =>
      // A bare <null> means an empty value where it's supported, so quoting it would match the
      // literal text "<null>" instead.
      value instanceof NullStringValueContext ? value.getText() : `"${getValueNodeValue(value)}"`,
    )
    .join('=');
  // Accepted unquoted values can hold a `*` too, and the quoted text quotes every value.
  const hasUnquotedAsterisk = values.some(
    (value) => !(value instanceof QuotedStringValueContext) && value.getText().includes('*'),
  );
  return {text, hasUnquotedAsterisk};
}

export class SelectionAutoCompleteVisitor extends BaseSelectionVisitor {
  private getAttributeResultsMatchingQuery: SelectionAutoCompleteProvider['getAttributeResultsMatchingQuery'];
  private getAttributeValueResultsMatchingQuery: SelectionAutoCompleteProvider['getAttributeValueResultsMatchingQuery'];
  private getAllResults: SelectionAutoCompleteProvider['getAllResults'];
  private getFunctionResultsMatchingQuery: SelectionAutoCompleteProvider['getFunctionResultsMatchingQuery'];
  private getSubstringResultMatchingQuery: SelectionAutoCompleteProvider['getSubstringResultMatchingQuery'];
  private createOperatorSuggestion: SelectionAutoCompleteProvider['createOperatorSuggestion'];
  private supportsTraversal: SelectionAutoCompleteProvider['supportsTraversal'];
  private supportsNot: SelectionAutoCompleteProvider['supportsNot'];

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
    supportsNot,
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
    supportsNot: SelectionAutoCompleteProvider['supportsNot'];
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
    this.supportsNot = supportsNot;
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
      this.startReplacementIndex = ctx.start?.start ?? 0;
      this.stopReplacementIndex = (ctx.stop?.stop ?? 0) + 1;
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
    const stopIndex = ctx.stop?.stop ?? 0;
    // A lone `"` lexes as an opening quote, so only a closing quote ends the value here.
    if (
      !(ctx.value() instanceof IncompleteLeftQuotedStringValueContext) &&
      this.cursorIndex >= stopIndex &&
      this.line[this.cursorIndex - 1] === '"' &&
      this.line[this.cursorIndex] !== '"'
    ) {
      this.addAfterExpressionResults(ctx);
      return;
    }
    this.startReplacementIndex = ctx.start?.start ?? 0;
    this.stopReplacementIndex = (ctx.stop?.stop ?? 0) + 1;

    const expression = ctx.parent instanceof AttributeExpressionContext ? ctx.parent : undefined;
    if (expression) {
      const colonToken = expression.colonToken();
      const postWhitespace = expression.postAttributeValueWhitespace();
      if (colonToken?.start) {
        this.startReplacementIndex = colonToken.start.start + 1;
      }
      if (postWhitespace?.start) {
        this.stopReplacementIndex = postWhitespace.start.start;
      }
    }

    const parentChildren = ctx.parent?.children ?? [];
    if (parentChildren[0] instanceof AttributeNameContext) {
      const rawValue = getValueNodeValue(ctx.value());
      const quotedValue = expression
        ? getQuotedValue(expression, this.supportsTraversal)
        : undefined;
      const key =
        expression?.attributeValue(1) === ctx
          ? getValueNodeValue(expression.attributeValue(0))
          : undefined;
      this.addAttributeValueResults(parentChildren[0].getText(), rawValue, {quotedValue, key});
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
        this.startReplacementIndex = (ctx.start?.start ?? 1) - 1;
        this.stopReplacementIndex = this.startReplacementIndex;
        if (attributeName) {
          this.addAttributeResults(attributeName.getText());
        }
      }
    }
  }

  public visitAttributeName(ctx: AttributeNameContext) {
    this.startReplacementIndex = ctx.start?.start ?? 0;
    this.stopReplacementIndex = (ctx.stop?.stop ?? 0) + 2;
    this.addAttributeResults(ctx.getText());
  }

  public visitOrToken(ctx: OrTokenContext) {
    const stopIndex = ctx.stop?.stop ?? 0;
    if (this.cursorIndex > stopIndex) {
      // Let whitespace token handle
    } else {
      this.startReplacementIndex = ctx.start?.start ?? 0;
      this.stopReplacementIndex = stopIndex + 1;
      this.list.push(
        this.createOperatorSuggestion({text: 'or', type: 'or', displayText: 'or'}),
        this.createOperatorSuggestion({text: 'and', type: 'and', displayText: 'and'}),
      );
    }
  }

  public visitAndToken(ctx: AndTokenContext) {
    const stopIndex = ctx.stop?.stop ?? 0;
    if (this.cursorIndex > stopIndex) {
      // Let whitespace token handle
    } else {
      this.startReplacementIndex = ctx.start?.start ?? 0;
      this.stopReplacementIndex = stopIndex + 1;
      this.list.push(
        this.createOperatorSuggestion({text: 'and', type: 'and', displayText: 'and'}),
        this.createOperatorSuggestion({text: 'or', type: 'or', displayText: 'or'}),
      );
    }
  }

  public visitUnmatchedValue(ctx: UnmatchedValueContext) {
    if (this.nodeIncludesCursor(ctx)) {
      this.startReplacementIndex = ctx.start?.start ?? 0;
      this.stopReplacementIndex = (ctx.stop?.stop ?? 0) + 1;
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
      this.startReplacementIndex = valueCtx.start?.start ?? 0;
      this.stopReplacementIndex = (valueCtx.stop?.stop ?? 0) + 1;
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
      this.startReplacementIndex = wsCtx?.start?.start ?? 0;
      this.stopReplacementIndex = this.startReplacementIndex;
      this.addAttributeValueResults(attrNameCtx.getText(), '');
    }
  }

  public visitIncompleteAttributeExpressionMissingSecondValue(
    ctx: IncompleteAttributeExpressionMissingSecondValueContext,
  ) {
    const attribute = ctx.attributeName().getText();
    const isKeyValueAttribute = (KEY_VALUE_ATTRIBUTES as readonly string[]).includes(attribute);
    if (!isKeyValueAttribute || this.cursorIndex <= ctx.EQUAL().symbol.start) {
      this.visitChildren(ctx);
      return;
    }
    const keyCtx = ctx.attributeValue();
    this.startReplacementIndex = keyCtx.start?.start ?? 0;
    this.stopReplacementIndex = this.cursorIndex;
    this.addAttributeValueResults(attribute, '', {key: getValueNodeValue(keyCtx)});
  }

  public visitPostNotOperatorWhitespace(ctx: PostNotOperatorWhitespaceContext) {
    const needsWhitespace = this.cursorIndex === (ctx.start?.start ?? 0);
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
    this.startReplacementIndex = ctx.start?.start ?? 0;
    this.stopReplacementIndex = ctx.stop?.stop ?? 0;
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
      const needsWhitespace = !isAfterLeftParen && this.cursorIndex === (ctx.start?.start ?? 0);
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
    // The substring row can't express a quote or backslash inside its quoted pattern.
    const canMatchSubstring = value !== '' && !/["\\]/.test(value);
    const substringResult = canMatchSubstring
      ? this.getSubstringResultMatchingQuery({query: value, textCallback})
      : null;
    if (substringResult) {
      this.list.push(substringResult);
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

    if (this.supportsNot && !options.excludeNot && 'not'.startsWith(value)) {
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
    attribute: string,
    value: string,
    {quotedValue, key}: AttributeValueResultsOptions = {},
  ) {
    const unquotedValue = removeQuotesFromString(value);
    this.list.push(
      ...this.getAttributeValueResultsMatchingQuery({
        attribute,
        query: unquotedValue,
        textCallback: DEFAULT_TEXT_CALLBACK,
        quotedValue,
        key,
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
