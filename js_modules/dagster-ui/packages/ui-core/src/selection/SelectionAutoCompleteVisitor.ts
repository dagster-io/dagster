import {ParserRuleContext} from 'antlr4ts';

import {BaseSelectionVisitor} from './BaseSelectionVisitor';
import {
  getValueNodeValue,
  isInsideExpressionlessParenthesizedExpression,
  removeQuotesFromString,
} from './SelectionInputUtil';
import {
  AllExpressionContext,
  AndTokenContext,
  AttributeNameContext,
  AttributeValueContext,
  ColonTokenContext,
  DownTraversalContext,
  FunctionNameContext,
  IncompleteAttributeExpressionMissingValueContext,
  IncompletePlusTraversalExpressionContext,
  LeftParenTokenContext,
  OrTokenContext,
  PostDownwardTraversalWhitespaceContext,
  PostLogicalOperatorWhitespaceContext,
  PostNeighborTraversalWhitespaceContext,
  PostNotOperatorWhitespaceContext,
  PostUpwardTraversalWhitespaceContext,
  UnmatchedValueContext,
  UpTraversalContext,
} from './generated/SelectionAutoCompleteParser';

const DEFAULT_TEXT_CALLBACK = (value: string) => value;

// set to true for debug output if desired
const DEBUG = false;

export type Suggestion =
  | {
      text: string;
      displayText?: string;
      type: 'function' | 'logical_operator' | 'parenthesis';
    }
  | {
      text: string;
      displayText?: string;
      type: 'attribute';
      attributeName?: string;
    }
  | {
      text: string;
      displayText?: string;
      type: 'traversal';
    };

export class SelectionAutoCompleteVisitor extends BaseSelectionVisitor {
  private attributesMap: Record<string, string[]>;
  private functions: string[];
  private nameBase: string;
  private attributesWithNameBase: string[];
  private allAttributes: {key: string; value: string}[];
  public list: Suggestion[] = [];

  // Replacement indices from the original code
  public _startReplacementIndex: number;
  public _stopReplacementIndex: number;

  constructor({
    attributesMap,
    functions,
    nameBase,
    line,
    cursorIndex,
  }: {
    attributesMap: Record<string, string[]>;
    functions: string[];
    nameBase: string;
    line: string;
    cursorIndex: number;
  }) {
    super({line, cursorIndex});
    this.attributesMap = attributesMap;
    this.functions = functions;
    this.nameBase = nameBase;
    this.attributesWithNameBase = [
      `${this.nameBase}_substring`,
      this.nameBase,
      ...Object.keys(attributesMap).filter((name) => name !== this.nameBase),
    ];
    this.allAttributes = Object.keys(attributesMap).flatMap((key) => {
      return (
        attributesMap[key]?.sort((a, b) => a.localeCompare(b)).map((value) => ({key, value})) ?? []
      );
    });
    this._startReplacementIndex = cursorIndex;
    this._stopReplacementIndex = cursorIndex;
  }

  // Keep the same accessors and logging as before
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

  // ----------------------------------------------------------------------------
  // The rest is the same node-specific logic from the original class
  // ----------------------------------------------------------------------------

  public visitAllExpression(ctx: AllExpressionContext) {
    if (this.nodeIncludesCursor(ctx.postExpressionWhitespace())) {
      this.visit(ctx.postExpressionWhitespace());
    } else {
      this.startReplacementIndex = this.cursorIndex;
      this.stopReplacementIndex = this.cursorIndex;
      this.addUnmatchedValueResults('', DEFAULT_TEXT_CALLBACK, {excludePlus: true});
      if (isInsideExpressionlessParenthesizedExpression(ctx)) {
        this.list.push({text: ')', displayText: ')', type: 'parenthesis' as const});
      }
    }
  }

  public visitUpTraversal(ctx: UpTraversalContext) {
    if (ctx.text.includes('+')) {
      this.list.push({text: '+', displayText: '+', type: 'traversal' as const});
    }
    this.list.push({text: '()', displayText: '(', type: 'parenthesis' as const});
  }

  public visitDownTraversal(ctx: DownTraversalContext) {
    this.list.push({text: ' and ', displayText: 'and', type: 'logical_operator' as const});
    this.list.push({text: ' or ', displayText: 'or', type: 'logical_operator' as const});
    if (ctx.text.includes('+')) {
      this.list.push({text: '+', displayText: '+', type: 'traversal' as const});
    }
    if (isInsideExpressionlessParenthesizedExpression(ctx)) {
      this.list.push({text: ')', displayText: ')', type: 'parenthesis' as const});
    }
  }

  public visitFunctionName(ctx: FunctionNameContext) {
    if (this.nodeIncludesCursor(ctx)) {
      this.startReplacementIndex = ctx.start.startIndex;
      this.stopReplacementIndex = ctx.stop!.stopIndex + 1;
      this.addFunctionResults(ctx.text);
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

    const parentChildren = ctx.parent?.children ?? [];
    if (parentChildren[0]?.constructor.name === 'AttributeNameContext') {
      const rawValue = getValueNodeValue(ctx.value());
      this.addAttributeValueResults(parentChildren[0].text, rawValue);
    }
  }

  public visitColonToken(ctx: ColonTokenContext) {
    if (this.nodeIncludesCursor(ctx)) {
      let attributeName: ParserRuleContext | null = null;
      let valueNode: ParserRuleContext | null = null;

      const parentChildren = ctx.parent?.children ?? [];
      if (parentChildren[0]?.constructor.name === 'AttributeNameContext') {
        attributeName = parentChildren[0] as ParserRuleContext;
      }
      if (parentChildren[1]?.constructor.name === 'AttributeValueContext') {
        valueNode = parentChildren[1] as ParserRuleContext;
      } else if (parentChildren[2]?.constructor.name === 'AttributeValueContext') {
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
        {text: 'or', displayText: 'or', type: 'logical_operator'},
        {text: 'and', displayText: 'and', type: 'logical_operator'},
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
        {text: 'and', displayText: 'and', type: 'logical_operator'},
        {text: 'or', displayText: 'or', type: 'logical_operator'},
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
      ...this.attributesWithNameBase
        .filter((attr) => attr.startsWith(value.trim()))
        .map((val) => {
          const suggestionValue = `${val}:`;
          return {
            text: textCallback(suggestionValue),
            displayText: suggestionValue,
            type: 'attribute' as const,
            attributeName: val,
          };
        }),
    );
  }

  private addFunctionResults(
    value: string,
    textCallback: (value: string) => string = DEFAULT_TEXT_CALLBACK,
    includeParenthesis: boolean = false,
  ) {
    this.list.push(
      ...this.functions
        .filter((fn) => fn.startsWith(value.trim()))
        .map((val) => {
          const suggestionValue = `${val}${includeParenthesis ? '()' : ''}`;
          return {
            text: textCallback(suggestionValue),
            displayText: suggestionValue,
            type: 'function' as const,
          };
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
      const substringMatchDisplayText = `${this.nameBase}_substring:${removeQuotesFromString(value)}`;
      const substringMatchText = `${this.nameBase}_substring:${addQuotesIfNecessary(removeQuotesFromString(value))} `;
      this.list.push({
        text: textCallback(substringMatchText),
        displayText: substringMatchDisplayText,
        type: 'attribute' as const,
        attributeName: `${this.nameBase}_substring`,
      });
    }
    this.addAttributeResults(value, textCallback);
    this.addFunctionResults(value, textCallback, true);

    if (value) {
      this.allAttributes.forEach((attribute) => {
        if (attribute.value.includes(value.toLowerCase())) {
          this.list.push({
            text: textCallback(`${attribute.key}:${addQuotesIfNecessary(attribute.value)} `),
            displayText: `${attribute.key}:${attribute.value}`,
            type: 'attribute' as const,
            attributeName: attribute.key,
          });
        }
      });
    }

    if (!options.excludeNot && 'not'.startsWith(value)) {
      this.list.push({
        text: textCallback('not '),
        displayText: 'not',
        type: 'logical_operator' as const,
      });
    }
    if (value === '') {
      if (!options.excludePlus) {
        this.list.push({
          text: textCallback('+'),
          displayText: '+',
          type: 'traversal' as const,
        });
      }
      this.list.push({
        text: textCallback('()'),
        displayText: '(',
        type: 'parenthesis' as const,
      });
    }
  }

  private addAttributeValueResults(
    attributeKey: string,
    value: string,
    textCallback: (value: string) => string = DEFAULT_TEXT_CALLBACK,
  ) {
    let possibleValues = this.attributesMap[attributeKey] ?? [];
    if (attributeKey === `${this.nameBase}_substring`) {
      possibleValues = this.attributesMap[this.nameBase]!;
    }
    const unquotedValue = removeQuotesFromString(value);
    possibleValues.forEach((attributeValue) => {
      if (attributeValue.includes(unquotedValue)) {
        this.list.push({
          text: `${textCallback(addQuotesIfNecessary(attributeValue))} `,
          displayText: attributeValue,
          type: 'attribute' as const,
          attributeName: attributeKey,
        });
      }
    });
  }

  private addAfterExpressionResults(
    ctx: ParserRuleContext,
    options: {
      excludePlus?: boolean;
    } = {},
  ) {
    this.list.push(
      {text: ' and ', displayText: 'and', type: 'logical_operator' as const},
      {text: ' or ', displayText: 'or', type: 'logical_operator' as const},
    );

    if (!options.excludePlus) {
      this.list.push({text: '+', displayText: '+', type: 'traversal' as const});
    }

    if (isInsideExpressionlessParenthesizedExpression(ctx)) {
      this.list.push({text: ')', displayText: ')', type: 'parenthesis' as const});
    }
  }
}

function addQuotesIfNecessary(value: string) {
  const doesContainSpecialCharacters = /[^\w]/.test(value);
  return doesContainSpecialCharacters ? `"${value}"` : value;
}
