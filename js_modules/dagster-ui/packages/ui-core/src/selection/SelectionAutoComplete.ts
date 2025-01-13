import {ParserRuleContext} from 'antlr4ts';
import {AbstractParseTreeVisitor} from 'antlr4ts/tree/AbstractParseTreeVisitor';
import {ParseTree} from 'antlr4ts/tree/ParseTree';
import {RuleNode} from 'antlr4ts/tree/RuleNode';
import CodeMirror from 'codemirror';

import {parseInput} from './SelectionAutoCompleteInputParser';
import {
  isInsideExpressionlessParenthesizedExpression,
  removeQuotesFromString,
} from './SelectionAutoCompleteUtil';
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
  ParenthesizedExpressionContext,
  PostAttributeValueWhitespaceContext,
  PostDownwardTraversalWhitespaceContext,
  PostLogicalOperatorWhitespaceContext,
  PostNeighborTraversalWhitespaceContext,
  PostNotOperatorWhitespaceContext,
  PostUpwardTraversalWhitespaceContext,
  UnmatchedValueContext,
  UpTraversalContext,
} from './generated/SelectionAutoCompleteParser';
import {SelectionAutoCompleteVisitor as _SelectionAutoCompleteVisitor} from './generated/SelectionAutoCompleteVisitor';

type Suggestion = {text: string; displayText?: string};
type TextCallback = (value: string) => string;
const DEFAULT_TEXT_CALLBACK = (value: string) => value;

// set to true for useful debug output.
const DEBUG = false;

export class SelectionAutoCompleteVisitor
  extends AbstractParseTreeVisitor<void>
  implements _SelectionAutoCompleteVisitor<void>
{
  private cursorIndex: number;
  private line: string;
  private attributesMap: Record<string, string[]>;
  private functions: string[];
  private nameBase: string;
  private attributesWithNameBase: string[];
  private allAttributes: {key: string; value: string}[];
  public list: Suggestion[] = [];
  public _startReplacementIndex: number = 0;
  public _stopReplacementIndex: number = 0;
  private forceVisitCtx = new WeakSet<any>();

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
    super();
    this.cursorIndex = cursorIndex;
    this.line = line;
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

  forceVisit(ctx: ParserRuleContext) {
    this.forceVisitCtx.add(ctx);
    ctx.accept(this);
  }

  visit(tree: ParseTree) {
    const _tree = tree as ParserRuleContext;
    if (
      _tree.start.startIndex !== undefined &&
      _tree.stop?.stopIndex !== undefined &&
      !this.nodeIncludesCursor(_tree) &&
      !this.forceVisitCtx.has(_tree)
    ) {
      if (!tree.parent) {
        // If we're at the root but not within the expression then we're at the whitespace before any expression.
        this.addUnmatchedValueResults('');
        this.startReplacementIndex = this.cursorIndex;
        this.stopReplacementIndex = this.cursorIndex;
      }
      return;
    }
    return super.visit(tree);
  }

  visitChildren(node: RuleNode): void {
    let result = this.defaultResult();
    const n = node.childCount;
    for (let i = 0; i < n; i++) {
      if (!this.shouldVisitNextChild(node, result)) {
        break;
      }
      const c = node.getChild(i) as any;
      if (c.start && c.stop) {
        const isWhitespace = c.constructor.name.endsWith('WhitespaceContext');
        if (
          !this.nodeIncludesCursor(c) &&
          (!isWhitespace || c.start.startIndex !== this.cursorIndex) &&
          !this.forceVisitCtx.has(c)
        ) {
          continue;
        }
        const nextChild = node.childCount - 1 > i ? (node.getChild(i + 1) as any) : null;
        if (
          !this.nodeIncludesCursor(c, 0) &&
          nextChild?.constructor.name.endsWith('WhitespaceContext') &&
          !this.forceVisitCtx.has(c)
        ) {
          // Let the whitespace handle the suggestion
          continue;
        }
      }
      if (DEBUG) {
        console.log('visiting child', c.constructor.name, c.text);
      }
      const childResult = c.accept(this);
      result = this.aggregateResult(result, childResult);
    }
    return result;
  }

  protected defaultResult() {}

  private nodeIncludesCursor(
    ctx: Pick<ParserRuleContext, 'start' | 'stop'>,
    modifier: number = -1,
  ): boolean {
    const start = ctx.start.startIndex;
    const stop = ctx.stop ? ctx.stop.stopIndex : ctx.start.startIndex;

    return Math.max(0, this.cursorIndex + modifier) >= start && this.cursorIndex + modifier <= stop;
  }

  private addAttributeResults(value: string, textCallback: TextCallback = DEFAULT_TEXT_CALLBACK) {
    this.list.push(
      ...this.attributesWithNameBase
        .filter((attr) => attr.startsWith(value.trim()))
        .map((val) => {
          const suggestionValue = `${val}:`;
          return {text: textCallback(suggestionValue), displayText: suggestionValue};
        }),
    );
  }

  private addFunctionResults(
    value: string,
    textCallback: TextCallback = DEFAULT_TEXT_CALLBACK,
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
          };
        }),
    );
  }

  public addUnmatchedValueResults(
    _value: string,
    textCallback: TextCallback = DEFAULT_TEXT_CALLBACK,
    options: {excludeNot?: boolean; excludePlus?: boolean} = {},
  ) {
    const value = _value.trim();
    if (value) {
      const substringMatchDisplayText = `${this.nameBase}_substring:${removeQuotesFromString(
        value,
      )}`;
      const substringMatchText = `${this.nameBase}_substring:"${removeQuotesFromString(value)}"`;
      this.list.push({
        text: textCallback(substringMatchText),
        displayText: substringMatchDisplayText,
      });
    }
    this.addAttributeResults(value, textCallback);
    this.addFunctionResults(value, textCallback, true);

    if (value) {
      this.allAttributes.forEach((attribute) => {
        if (attribute.value.includes(value.toLowerCase())) {
          this.list.push({
            text: textCallback(`${attribute.key}:"${attribute.value}"`),
            displayText: `${attribute.key}:${attribute.value}`,
          });
        }
      });
    }

    if (!options.excludeNot && 'not'.startsWith(value)) {
      this.list.push({text: textCallback('not '), displayText: 'not'});
    }
    if (value === '') {
      if (!options.excludePlus) {
        this.list.push({text: textCallback('+'), displayText: '+'});
      }
      this.list.push({text: textCallback('()'), displayText: '('});
    }
  }

  private addAttributeValueResults(
    attributeKey: string,
    value: string,
    textCallback: TextCallback = DEFAULT_TEXT_CALLBACK,
  ) {
    let possibleValues = this.attributesMap[attributeKey] ?? [];
    if (attributeKey === `${this.nameBase}_substring`) {
      possibleValues = this.attributesMap[this.nameBase]!;
    }
    const unquotedValue = removeQuotesFromString(value);
    possibleValues.forEach((attributeValue) => {
      if (attributeValue.includes(unquotedValue)) {
        this.list.push({
          text: textCallback(`"${attributeValue}"`),
          displayText: attributeValue,
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
    this.list.push({text: ' and ', displayText: 'and'}, {text: ' or ', displayText: 'or'});

    if (!options.excludePlus) {
      this.list.push({text: '+', displayText: '+'});
    }

    if (isInsideExpressionlessParenthesizedExpression(ctx)) {
      this.list.push({text: ')', displayText: ')'});
    }
  }

  visitAllExpression(ctx: AllExpressionContext) {
    if (this.nodeIncludesCursor(ctx.postExpressionWhitespace())) {
      this.visit(ctx.postExpressionWhitespace());
    } else {
      this.startReplacementIndex = this.cursorIndex;
      this.stopReplacementIndex = this.cursorIndex;
      this.addUnmatchedValueResults('', DEFAULT_TEXT_CALLBACK, {
        excludePlus: true,
      });
      if (isInsideExpressionlessParenthesizedExpression(ctx)) {
        this.list.push({text: ')', displayText: ')'});
      }
    }
  }

  visitUpTraversal(ctx: UpTraversalContext) {
    if (ctx.text.includes('+')) {
      this.list.push({text: '+', displayText: '+'});
    }
    this.list.push({text: '()', displayText: '('});
  }

  visitDownTraversal(ctx: DownTraversalContext) {
    this.list.push({text: ' and ', displayText: 'and'});
    this.list.push({text: ' or ', displayText: 'or'});
    if (ctx.text.includes('+')) {
      this.list.push({text: '+', displayText: '+'});
    }
    if (isInsideExpressionlessParenthesizedExpression(ctx)) {
      this.list.push({text: ')', displayText: ')'});
    }
  }

  visitParenthesizedExpression(ctx: ParenthesizedExpressionContext) {
    if (this.nodeIncludesCursor(ctx.leftParenToken())) {
      // Move the cursor to the right and visit that expression.
      this.cursorIndex += 1;
    }
    this.visitChildren(ctx);
  }

  visitFunctionName(ctx: FunctionNameContext) {
    if (this.nodeIncludesCursor(ctx)) {
      this.startReplacementIndex = ctx.start.startIndex;
      this.stopReplacementIndex = ctx.stop!.stopIndex + 1;
      this.addFunctionResults(ctx.text);
    }
  }

  visitAttributeValue(ctx: AttributeValueContext) {
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
      this.addAttributeValueResults(parentChildren[0].text, getValue(ctx.value()));
    }
  }

  visitColonToken(ctx: ColonTokenContext) {
    if (this.nodeIncludesCursor(ctx)) {
      let attributeName: any;

      let valueNode: ParserRuleContext | null = null;
      const parentChildren = ctx.parent?.children ?? [];
      if (parentChildren[0]?.constructor.name === 'AttributeNameContext') {
        attributeName = parentChildren[0];
      }
      if (parentChildren[1]?.constructor.name === 'AttributeValueContext') {
        valueNode = parentChildren[1] as any;
      } else if (parentChildren[2]?.constructor.name === 'AttributeValueContext') {
        valueNode = parentChildren[2] as any;
      }
      if (attributeName?.stop && this.cursorIndex >= attributeName.stop?.stopIndex) {
        this.addAttributeValueResults(attributeName, getValue(valueNode));
      } else {
        this.startReplacementIndex = ctx.start.startIndex - 1;
        this.stopReplacementIndex = this.startReplacementIndex;
        this.addAttributeResults(attributeName);
      }
    }
  }

  visitAttributeName(ctx: AttributeNameContext) {
    this.startReplacementIndex = ctx.start.startIndex;
    this.stopReplacementIndex = ctx.stop!.stopIndex + 2;
    this.addAttributeResults(ctx.text);
  }

  visitOrToken(ctx: OrTokenContext) {
    if (this.cursorIndex > ctx.stop!.stopIndex) {
      // Let whitespace token handle this
    } else {
      this.startReplacementIndex = ctx.start.startIndex;
      this.stopReplacementIndex = ctx.stop!.stopIndex + 1;
      this.list.push({text: 'or', displayText: 'or'}, {text: 'and', displayText: 'and'});
    }
  }

  visitAndToken(ctx: AndTokenContext) {
    if (this.cursorIndex > ctx.stop!.stopIndex) {
      // Let whitespace token handle this
    } else {
      this.startReplacementIndex = ctx.start.startIndex;
      this.stopReplacementIndex = ctx.stop!.stopIndex + 1;
      this.list.push({text: 'and', displayText: 'and'}, {text: 'or', displayText: 'or'});
    }
  }

  visitUnmatchedValue(ctx: UnmatchedValueContext) {
    if (this.nodeIncludesCursor(ctx)) {
      this.startReplacementIndex = ctx.start.startIndex;
      this.stopReplacementIndex = ctx.stop!.stopIndex + 1;
      this.addUnmatchedValueResults(ctx.text);
    }
  }

  visitIncompletePlusTraversalExpression(ctx: IncompletePlusTraversalExpressionContext) {
    if (
      this.nodeIncludesCursor(ctx.postNeighborTraversalWhitespace()) &&
      ctx.postNeighborTraversalWhitespace().text.length
    ) {
      return this.visit(ctx.postNeighborTraversalWhitespace());
    }
    this.addUnmatchedValueResults('', DEFAULT_TEXT_CALLBACK, {
      excludeNot: true,
    });
  }

  visitIncompleteAttributeExpressionMissingValue(
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

  visitPostNotOperatorWhitespace(ctx: PostNotOperatorWhitespaceContext) {
    const needsWhitespace = this.cursorIndex === ctx.start.startIndex;
    this.addUnmatchedValueResults('', (value) => `${needsWhitespace ? ' ' : ''}${value}`, {
      excludeNot: true,
    });
  }

  visitPostNeighborTraversalWhitespace(_ctx: PostNeighborTraversalWhitespaceContext) {
    this.addUnmatchedValueResults('', DEFAULT_TEXT_CALLBACK);
  }

  visitPostUpwardTraversalWhitespace(_ctx: PostUpwardTraversalWhitespaceContext) {
    this.addUnmatchedValueResults('', DEFAULT_TEXT_CALLBACK, {
      excludePlus: true,
    });
  }

  visitPostDownwardTraversalWhitespace(ctx: PostDownwardTraversalWhitespaceContext) {
    this.addAfterExpressionResults(ctx, {
      excludePlus: true,
    });
  }

  visitPostExpressionWhitespace(ctx: ParserRuleContext) {
    if (!this.list.length) {
      this.addAfterExpressionResults(ctx);
    }
  }

  // This is visited even if the whitespace has length 0.
  visitPostLogicalOperatorWhitespace(ctx: PostLogicalOperatorWhitespaceContext) {
    // Check if anything before us already made suggestions
    // Since we get called even if the previous token handled it
    if (!this.list.length) {
      const isAfterNot = this.line.slice(0, this.cursorIndex).trim().toLowerCase().endsWith('not');

      const isAfterLeftParen = this.line[this.cursorIndex - 1] === '(';

      // If the cursor is at the start then we need a space before...
      const needsWhitespace = !isAfterLeftParen && this.cursorIndex === ctx.start.startIndex;
      this.addUnmatchedValueResults('', (text) => `${needsWhitespace ? ' ' : ''}${text}`, {
        excludeNot: isAfterNot,
      });
    }
  }

  visitPostAttributeValueWhitespace(ctx: PostAttributeValueWhitespaceContext) {
    const attributeValue = ctx.parent!.getChild(2) as any;
    if (this.cursorIndex === attributeValue?.stop?.stopIndex + 1) {
      this.forceVisit(attributeValue);
    } else {
      this.visitPostExpressionWhitespace(ctx);
    }
  }

  visitLeftParenToken(_ctx: LeftParenTokenContext) {
    this.addUnmatchedValueResults('');
  }
}

export function createSelectionHint<T extends Record<string, string[]>, N extends keyof T>({
  nameBase: _nameBase,
  attributesMap,
  functions,
}: {
  nameBase: N;
  attributesMap: T;
  functions: string[];
}): CodeMirror.HintFunction {
  const nameBase = _nameBase as string;

  return function (cm: CodeMirror.Editor, _options: CodeMirror.ShowHintOptions): any {
    const line = cm.getLine(0);
    const {parseTrees} = parseInput(line);

    let start = 0;
    const actualCursorIndex = cm.getCursor().ch;

    let visitorWithAutoComplete;
    if (!parseTrees.length) {
      // Special case empty string to add unmatched value results
      visitorWithAutoComplete = new SelectionAutoCompleteVisitor({
        attributesMap,
        functions,
        nameBase,
        line,
        cursorIndex: actualCursorIndex,
      });
      start = actualCursorIndex;
      visitorWithAutoComplete.addUnmatchedValueResults('');
    } else {
      for (const {tree, line} of parseTrees) {
        const cursorIndex = actualCursorIndex - start;
        const visitor = new SelectionAutoCompleteVisitor({
          attributesMap,
          functions,
          nameBase,
          line,
          cursorIndex,
        });
        visitor.visit(tree);
        const length = line.length;
        if (cursorIndex <= length) {
          visitorWithAutoComplete = visitor;
          break;
        }
        start += length;
      }
    }
    if (visitorWithAutoComplete) {
      return {
        list: visitorWithAutoComplete.list,
        from: cm.posFromIndex(start + visitorWithAutoComplete.startReplacementIndex),
        to: cm.posFromIndex(start + visitorWithAutoComplete.stopReplacementIndex),
      };
    }
  };
}

function getValue(ctx: ParserRuleContext | null) {
  switch (ctx?.constructor.name) {
    case 'UnquotedStringValueContext': {
      return ctx.text;
    }
    case 'IncompleteLeftQuotedStringValueContext': {
      return ctx.text.slice(1);
    }
    case 'IncompleteRightQuotedStringValueContext': {
      return ctx.text.slice(0, -1);
    }
    case 'QuotedStringValueContext': {
      return ctx.text.slice(1, -1);
    }
    case 'AttributeValueContext': {
      return getValue((ctx as AttributeValueContext).value());
    }
  }
  return ctx?.text ?? '';
}
