// AutoCompleteSuggestionVisitor.ts

import {ParserRuleContext} from 'antlr4ts';
import {AbstractParseTreeVisitor} from 'antlr4ts/tree/AbstractParseTreeVisitor';
import CodeMirror from 'codemirror';

import {
  AllExpressionContext,
  AndExpressionContext,
  AttributeExpressionContext,
  AttributeNameContext,
  DownTraversalExpressionContext,
  ExpressionlessFunctionExpressionContext,
  ExpressionlessParenthesizedExpressionContext,
  FunctionCallExpressionContext,
  FunctionNameContext,
  IncompleteAndExpressionContext,
  IncompleteAttributeExpressionContext,
  IncompleteNotExpressionContext,
  IncompleteOrExpressionContext,
  IncompleteTraversalExpressionContext,
  NotExpressionContext,
  OrExpressionContext,
  ParenthesizedExpressionContext,
  QuotedStringValueContext,
  StartContext,
  TraversalContext,
  UnclosedExpressionlessFunctionExpressionContext,
  UnclosedExpressionlessParenthesizedExpressionContext,
  UnmatchedValueContext,
  UnquotedStringValueContext,
  UpAndDownTraversalExpressionContext,
  UpTraversalExpressionContext,
} from './generated/SelectionAutoCompleteParser';
import {SelectionAutoCompleteVisitor as _SelectionAutoCompleteVisitor} from './generated/SelectionAutoCompleteVisitor';

type Suggestion = {text: string; displayText?: string};
type TextCallback = (value: string) => string;
const DEFAULT_TEXT_CALLBACK = (value: string) => value;

export class SelectionAutoCompleteVisitor
  extends AbstractParseTreeVisitor<void>
  implements _SelectionAutoCompleteVisitor<void>
{
  private cm: CodeMirror.Editor;
  private cursorIndex: number;
  private line: string;
  private attributesMap: Record<string, string[]>;
  private functions: string[];
  private nameBase: string;
  private attributesWithNameBase: string[];
  private allAttributes: {key: string; value: string}[];
  public list: Suggestion[] = [];
  public startReplacementIndex: number = 0;
  public stopReplacementIndex: number = 0;
  private currentNode: ParserRuleContext | null = null;

  constructor(
    cm: CodeMirror.Editor,
    attributesMap: Record<string, string[]>,
    functions: string[],
    nameBase: string,
  ) {
    super();
    this.cm = cm;
    const cursor = cm.getCursor();
    this.cursorIndex = Math.max(0, cm.indexFromPos(cursor) - 1);
    this.line = cm.getLine(0);
    this.attributesMap = attributesMap;
    this.functions = functions;
    this.nameBase = nameBase;
    this.attributesWithNameBase = [
      `${this.nameBase}_substring`,
      this.nameBase,
      ...Object.keys(attributesMap).filter((name) => name !== this.nameBase),
    ];
    this.allAttributes = Object.keys(attributesMap).flatMap((key) => {
      return attributesMap[key]?.map((value) => ({key, value})) ?? [];
    });
  }

  protected defaultResult() {}

  private nodeIncludesCursor(ctx: ParserRuleContext): boolean {
    const start = ctx.start.startIndex;
    const stop = ctx.stop ? ctx.stop.stopIndex : ctx.start.startIndex;
    return this.cursorIndex >= start && this.cursorIndex <= stop;
  }

  private addAttributeResults(value: string, textCallback: TextCallback = DEFAULT_TEXT_CALLBACK) {
    this.list.push(
      ...this.attributesWithNameBase
        .filter((attr) => attr.includes(value))
        .map((val) => {
          const suggestionValue = `${val}:`;
          return {text: textCallback(suggestionValue), displayText: suggestionValue};
        }),
    );
  }

  private addFunctionResults(value: string, textCallback: TextCallback = DEFAULT_TEXT_CALLBACK) {
    this.list.push(
      ...this.functions
        .filter((fn) => fn.includes(value))
        .map((val) => {
          const suggestionValue = `${val}()`;
          return {
            text: textCallback(suggestionValue),
            displayText: suggestionValue,
          };
        }),
    );
  }

  private addUnmatchedValueResults(
    value: string,
    textCallback: TextCallback = DEFAULT_TEXT_CALLBACK,
  ) {
    if (value) {
      const substringMatchDisplayText = `${this.nameBase}_substring:${removeQuotesFromString(
        value,
      )}`;
      const substringMatchText = `${this.nameBase}_substring:"${removeQuotesFromString(value)}"`;
      this.list.push({
        text: textCallback(substringMatchText),
        displayText: substringMatchDisplayText,
      });
      this.allAttributes.forEach((attribute) => {
        if (attribute.value.includes(value)) {
          this.list.push({
            text: textCallback(`${attribute.key}:"${attribute.value}"`),
            displayText: `${attribute.key}:${attribute.value}`,
          });
        }
      });
    }
    this.addAttributeResults(value, textCallback);
    this.addFunctionResults(value, textCallback);

    if (value === '') {
      this.list.push({text: 'not ', displayText: 'not'});
      this.list.push({text: '*'}, {text: '+'}, {text: '()', displayText: '('});
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
    possibleValues.forEach((attributeValue) => {
      if (attributeValue.includes(removeQuotesFromString(value))) {
        this.list.push({
          text: textCallback(`"${attributeValue}"`),
          displayText: attributeValue,
        });
      }
    });
  }

  // Visit methods for each node type
  visitStart(ctx: StartContext) {
    if (this.nodeIncludesCursor(ctx)) {
      this.currentNode = ctx;
      this.startReplacementIndex = ctx.start.startIndex;
      this.stopReplacementIndex = ctx.stop!.stopIndex + 1;
      this.visit(ctx.expr());
    }
  }

  visitAllExpression(ctx: AllExpressionContext) {
    if (this.nodeIncludesCursor(ctx)) {
      if (isInsideExpressionlessParenthesizedExpression(ctx)) {
        this.list.push({text: ')'});
      }
      // No need to visit children
      return;
    }
  }

  visitIncompleteTraversalExpression(ctx: IncompleteTraversalExpressionContext) {
    if (this.nodeIncludesCursor(ctx)) {
      // Handle suggestions for incomplete traversal
      // No specific suggestions in original logic
      return;
    }
  }

  visitTraversal(ctx: TraversalContext) {
    // Traversal is handled within other contexts
  }

  visitDownTraversalExpression(ctx: DownTraversalExpressionContext) {
    if (this.nodeIncludesCursor(ctx)) {
      const traversal = ctx.traversal();
      const expr = ctx.traversalAllowedExpr();

      if (this.nodeIncludesCursor(traversal)) {
        // Cursor is within traversal operator
        // No specific suggestions
        return;
      } else if (this.nodeIncludesCursor(expr)) {
        this.visit(expr);
        return;
      } else {
        // After traversal operator
        this.startReplacementIndex = this.cursorIndex;
        this.stopReplacementIndex = this.cursorIndex;
        this.list.push({text: ' and ', displayText: 'and'});
        this.list.push({text: ' or ', displayText: 'or'});
        if (ctx.traversal().text.includes('+')) {
          this.list.push({text: '+'});
        }
        if (isInsideExpressionlessParenthesizedExpression(ctx)) {
          this.list.push({text: ')'});
        }
        return;
      }
    }
  }

  visitUpTraversalExpression(ctx: UpTraversalExpressionContext) {
    if (this.nodeIncludesCursor(ctx)) {
      const traversal = ctx.traversal();
      const expr = ctx.traversalAllowedExpr();

      if (this.nodeIncludesCursor(traversal)) {
        // Cursor is within traversal operator
        // No specific suggestions
        return;
      } else if (this.nodeIncludesCursor(expr)) {
        this.visit(expr);
        return;
      } else {
        // After traversal operator
        this.startReplacementIndex = this.cursorIndex;
        this.stopReplacementIndex = this.cursorIndex;
        this.list.push({text: '(', displayText: '('});
        return;
      }
    }
  }

  visitUpAndDownTraversalExpression(ctx: UpAndDownTraversalExpressionContext) {
    if (this.nodeIncludesCursor(ctx)) {
      // Similar handling as up and down traversal expressions
      this.visit(ctx.traversalAllowedExpr());
      return;
    }
  }

  visitAttributeName(ctx: AttributeNameContext) {
    if (this.nodeIncludesCursor(ctx)) {
      this.stopReplacementIndex = ctx.stop!.stopIndex + 1;
      this.addAttributeResults(ctx.text);
    }
  }

  visitIncompleteAttributeExpression(ctx: IncompleteAttributeExpressionContext) {
    if (this.nodeIncludesCursor(ctx)) {
      const keyNode = ctx.attributeName();
      const key = keyNode.text;

      this.startReplacementIndex = keyNode.stop!.stopIndex + 1; // After colon
      this.stopReplacementIndex = keyNode.stop!.stopIndex + 1;
      this.addAttributeValueResults(key, '');
      return;
    }
  }

  visitParenthesizedExpression(ctx: ParenthesizedExpressionContext) {
    if (this.nodeIncludesCursor(ctx)) {
      if (this.cursorIndex === ctx.stop!.stopIndex) {
        this.startReplacementIndex = ctx.stop!.stopIndex + 1;
        this.stopReplacementIndex = ctx.stop!.stopIndex + 1;
        this.list.push({text: ' and ', displayText: 'and'}, {text: ' or ', displayText: 'or'});
        if (this.line[this.stopReplacementIndex] !== '*') {
          this.list.push({text: '+'});
          if (this.line[this.startReplacementIndex] !== '+') {
            this.list.push({text: '*'});
          }
        }
        if (isInsideExpressionlessParenthesizedExpression(ctx)) {
          this.list.push({text: ')'});
        }
        return;
      }
      this.visit(ctx.expr());
    }
  }

  visitIncompleteNotExpression(ctx: IncompleteNotExpressionContext) {
    if (this.nodeIncludesCursor(ctx)) {
      this.startReplacementIndex = this.cursorIndex + 1;
      this.stopReplacementIndex = this.cursorIndex + 1;
      let needsSpaceBefore = false;
      if (this.line[this.cursorIndex] !== ' ') {
        needsSpaceBefore = true;
      }
      this.addUnmatchedValueResults('', (text) => `${needsSpaceBefore ? ' ' : ''}${text}`);
      return;
    }
  }

  visitIncompleteAndExpression(ctx: IncompleteAndExpressionContext) {
    if (this.nodeIncludesCursor(ctx)) {
      this.startReplacementIndex = this.cursorIndex + 1;
      this.stopReplacementIndex = this.cursorIndex + 1;
      let needsSpaceBefore = false;
      if (this.line[this.cursorIndex] !== ' ') {
        needsSpaceBefore = true;
      }
      this.addUnmatchedValueResults('', (text) => `${needsSpaceBefore ? ' ' : ''}${text}`);
      return;
    }
  }

  visitIncompleteOrExpression(ctx: IncompleteOrExpressionContext) {
    if (this.nodeIncludesCursor(ctx)) {
      this.startReplacementIndex = this.cursorIndex + 1;
      this.stopReplacementIndex = this.cursorIndex + 1;
      let needsSpaceBefore = false;
      if (this.line[this.cursorIndex] !== ' ') {
        needsSpaceBefore = true;
      }
      this.addUnmatchedValueResults('', (text) => `${needsSpaceBefore ? ' ' : ''}${text}`);
      return;
    }
  }

  visitFunctionName(ctx: FunctionNameContext) {
    if (this.nodeIncludesCursor(ctx)) {
      this.addFunctionResults(ctx.text);
    }
  }

  visitAttributeExpression(ctx: AttributeExpressionContext) {
    if (this.nodeIncludesCursor(ctx)) {
      const keyNode = ctx.attributeName();
      const valueNode = ctx.value();
      const attributeKey = keyNode.text;
      const nodeValue = valueNode.text;

      this.startReplacementIndex = valueNode.start.startIndex;
      this.stopReplacementIndex = valueNode.stop!.stopIndex + 1;
      this.addAttributeValueResults(attributeKey, nodeValue);
      return;
    }
  }

  visitFunctionCallExpression(ctx: FunctionCallExpressionContext) {
    if (this.nodeIncludesCursor(ctx)) {
      if (this.cursorIndex === ctx.stop!.stopIndex) {
        this.startReplacementIndex = ctx.stop!.stopIndex + 1;
        this.stopReplacementIndex = ctx.stop!.stopIndex + 1;
        this.list.push({text: ' and ', displayText: 'and'}, {text: ' or ', displayText: 'or'});
        if (this.line[this.stopReplacementIndex] !== '*') {
          this.list.push({text: '+'});
          if (this.line[this.startReplacementIndex] !== '+') {
            this.list.push({text: '*'});
          }
        }
        if (isInsideExpressionlessParenthesizedExpression(ctx)) {
          this.list.push({text: ')'});
        }
        return;
      }
      this.visit(ctx.functionAllowedExpr());
    }
  }

  visitQuotedStringValue(ctx: QuotedStringValueContext) {
    if (this.nodeIncludesCursor(ctx)) {
      if (ctx.parent instanceof UnmatchedValueContext) {
        this.addUnmatchedValueResults(ctx.text);
        return;
      }
      if (this.cursorIndex === ctx.stop!.stopIndex) {
        this.startReplacementIndex = ctx.stop!.stopIndex + 1;
        this.stopReplacementIndex = ctx.stop!.stopIndex + 1;
        this.list.push({text: ' and ', displayText: 'and'}, {text: ' or ', displayText: 'or'});
        if (this.line[this.stopReplacementIndex] !== '*') {
          this.list.push({text: '+'});
          if (this.line[this.startReplacementIndex] !== '+') {
            this.list.push({text: '*'});
          }
        }
        if (isInsideExpressionlessParenthesizedExpression(ctx)) {
          this.list.push({text: ')'});
        }
        return;
      }
      const nodeValue = getValueNodeValue(ctx);
      if (ctx.parent instanceof AttributeExpressionContext) {
        const attributeKey = ctx.parent.attributeName().text;
        this.addAttributeValueResults(attributeKey, nodeValue);
      }
    }
  }

  visitUnquotedStringValue(ctx: UnquotedStringValueContext) {
    if (this.nodeIncludesCursor(ctx)) {
      if (ctx.parent instanceof UnmatchedValueContext) {
        this.addUnmatchedValueResults(ctx.text);
        return;
      }
      const nodeValue = getValueNodeValue(ctx);
      if (ctx.parent instanceof AttributeExpressionContext) {
        const attributeKey = ctx.parent.attributeName().text;
        this.addAttributeValueResults(attributeKey, nodeValue);
      }
    }
  }

  visitAndExpression(ctx: AndExpressionContext) {
    if (this.nodeIncludesCursor(ctx)) {
      this.visit(ctx.expr(0));
      this.visit(ctx.expr(1));
    }
  }

  visitOrExpression(ctx: OrExpressionContext) {
    if (this.nodeIncludesCursor(ctx)) {
      this.visit(ctx.expr(0));
      this.visit(ctx.expr(1));
    }
  }

  visitNotExpression(ctx: NotExpressionContext) {
    if (this.nodeIncludesCursor(ctx)) {
      this.visit(ctx.expr());
    }
  }

  visitExpressionlessParenthesizedExpression(ctx: ExpressionlessParenthesizedExpressionContext) {
    if (this.nodeIncludesCursor(ctx)) {
      const char = this.line[this.cursorIndex];
      if (char !== ')') {
        this.addUnmatchedValueResults('');
      }
    }
  }

  visitUnclosedExpressionlessParenthesizedExpression(
    ctx: UnclosedExpressionlessParenthesizedExpressionContext,
  ) {
    if (this.nodeIncludesCursor(ctx)) {
      this.addUnmatchedValueResults('');
    }
  }

  visitExpressionlessFunctionExpression(ctx: ExpressionlessFunctionExpressionContext) {
    if (this.nodeIncludesCursor(ctx)) {
      this.addUnmatchedValueResults('');
    }
  }

  visitUnclosedExpressionlessFunctionExpression(
    ctx: UnclosedExpressionlessFunctionExpressionContext,
  ) {
    if (this.nodeIncludesCursor(ctx)) {
      this.addUnmatchedValueResults('');
    }
  }

  visitUnmatchedValue(ctx: UnmatchedValueContext) {
    if (this.nodeIncludesCursor(ctx)) {
      this.addUnmatchedValueResults(ctx.text);
    }
  }
}
