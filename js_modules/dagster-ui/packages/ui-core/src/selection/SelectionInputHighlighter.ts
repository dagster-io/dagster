import {Colors, FontFamily, TextInputStyles} from '@dagster-io/ui-components';
import {ParserRuleContext} from 'antlr4ts';
import {AbstractParseTreeVisitor} from 'antlr4ts/tree/AbstractParseTreeVisitor';
import CodeMirror from 'codemirror';
import {css} from 'styled-components';

import {SyntaxError} from './CustomErrorListener';
import {parseInput} from './SelectionInputParser';
import {
  AllExpressionContext,
  AttributeExpressionContext,
  AttributeNameContext,
  AttributeValueContext,
  DownTraversalContext,
  FunctionNameContext,
  IncompleteAttributeExpressionMissingKeyContext,
  IncompleteAttributeExpressionMissingValueContext,
  IncompletePlusTraversalExpressionContext,
  NullStringValueContext,
  ParenthesizedExpressionContext,
  PostAttributeValueWhitespaceContext,
  QuotedStringValueContext,
  StartContext,
  UnquotedStringValueContext,
  UpTraversalContext,
} from './generated/SelectionAutoCompleteParser';
import {SelectionAutoCompleteVisitor} from './generated/SelectionAutoCompleteVisitor';

export class SyntaxHighlightingVisitor
  extends AbstractParseTreeVisitor<void>
  implements SelectionAutoCompleteVisitor<void>
{
  private cm: CodeMirror.Editor;
  private startOffset: number;
  private cursorIndex: number;

  constructor(cm: CodeMirror.Editor, startOffSet: number, cursorIndex: number) {
    super();
    this.cm = cm;
    this.startOffset = startOffSet;
    this.cursorIndex = cursorIndex;
  }

  protected defaultResult() {}

  private addClass(ctx: ParserRuleContext, klass: string) {
    const from = this.cm.posFromIndex(this.startOffset + ctx.start.startIndex);
    const to = this.cm.posFromIndex(from.ch + ctx.text.length);
    this.cm.markText(from, to, {className: klass});
  }

  private addClassPos(fromIndex: number, toIndex: number, klass: string) {
    const from = this.cm.posFromIndex(this.startOffset + fromIndex);
    const to = this.cm.posFromIndex(this.startOffset + toIndex + 1);
    this.cm.markText(from, to, {className: klass});
  }

  private addActiveClass(ctx: ParserRuleContext, klass: string = 'active') {
    if (ctx.start.startIndex < this.cursorIndex && (ctx.stop?.stopIndex ?? 0) < this.cursorIndex) {
      this.addClass(ctx, klass);
    }
  }

  // Visit methods
  visitStart(ctx: StartContext) {
    this.visit(ctx.expr());
  }

  visitIncompleteAttributeExpressionMissingValue(
    ctx: IncompleteAttributeExpressionMissingValueContext,
  ) {
    this.addClass(ctx, 'expression attribute-expression');
    this.visitChildren(ctx);
  }
  visitIncompleteAttributeExpressionMissingKey(
    ctx: IncompleteAttributeExpressionMissingKeyContext,
  ) {
    const start = ctx.start.startIndex;
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    let end = ctx.stop!.stopIndex;
    if (ctx.postExpressionWhitespace()) {
      end = ctx.postExpressionWhitespace().start.startIndex;
    }
    this.addClassPos(start, end, 'expression attribute-expression');
    this.visitChildren(ctx);
  }

  visitAttributeExpression(ctx: AttributeExpressionContext) {
    const start = ctx.start.startIndex;
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    let end = ctx.stop!.stopIndex;
    if (ctx.postAttributeValueWhitespace()) {
      end = ctx.postAttributeValueWhitespace().start.startIndex;
    }
    this.addClassPos(start, end, 'expression attribute-expression');
    this.visitChildren(ctx);
  }

  visitAttributeName(ctx: AttributeNameContext) {
    this.addClass(ctx, `attribute-name attribute-${ctx.text}`);
    this.visitChildren(ctx);
  }

  visitAttributeValue(ctx: AttributeValueContext) {
    this.addClass(ctx, `attribute-value`);
    this.visitChildren(ctx);
  }

  visitFunctionName(ctx: FunctionNameContext) {
    this.addClass(ctx, `function-name function-${ctx.text}`);
    this.visitChildren(ctx);
  }

  visitQuotedStringValue(ctx: QuotedStringValueContext) {
    this.addClass(ctx, 'value');
    this.visitChildren(ctx);
  }

  visitUnquotedStringValue(ctx: UnquotedStringValueContext) {
    this.addClass(ctx, 'value');
    this.visitChildren(ctx);
  }

  visitNullStringValue(ctx: NullStringValueContext) {
    this.addClass(ctx, 'value');
    this.visitChildren(ctx);
  }

  visitAllExpression(ctx: AllExpressionContext) {
    this.addClass(ctx, 'expression value');
    this.visitChildren(ctx);
  }
  visitIncompleteLeftQuotedStringValue(ctx: ParserRuleContext) {
    this.addClass(ctx, 'value');
    this.visitChildren(ctx);
  }
  visitIncompleteRightQuotedStringValue(ctx: ParserRuleContext) {
    this.addClass(ctx, 'value');
    this.visitChildren(ctx);
  }
  visitTraversalAllowedExpression(ctx: ParserRuleContext) {
    this.addClass(ctx, 'expression');
    this.visitChildren(ctx);
  }
  visitUpAndDownTraversalExpression(ctx: ParserRuleContext) {
    this.addClass(ctx, 'expression');
    this.visitChildren(ctx);
  }
  visitUpTraversalExpression(ctx: ParserRuleContext) {
    this.addClass(ctx, 'expression');
    this.visitChildren(ctx);
  }
  visitUpTraversal(ctx: UpTraversalContext) {
    this.addClass(ctx, 'traversal');
  }
  visitDownTraversal(ctx: DownTraversalContext) {
    this.addClass(ctx, 'traversal');
  }
  visitIncompletePlusTraversalExpression(ctx: IncompletePlusTraversalExpressionContext) {
    this.addClass(ctx, 'traversal');
    this.visitChildren(ctx);
  }
  visitNotExpression(ctx: ParserRuleContext) {
    this.addClass(ctx, 'expression');
    this.visitChildren(ctx);
  }
  visitOrExpression(ctx: ParserRuleContext) {
    this.addClass(ctx, 'expression');
    this.visitChildren(ctx);
  }
  visitAndExpression(ctx: ParserRuleContext) {
    this.addClass(ctx, 'expression');
    this.visitChildren(ctx);
  }
  visitIncompleteAttributeExpressionMissingSecondValue(ctx: ParserRuleContext) {
    this.addClass(ctx, 'expression');
    this.visitChildren(ctx);
  }
  visitIncompleteNotExpression(ctx: ParserRuleContext) {
    this.addClass(ctx, 'expression');
    this.visitChildren(ctx);
  }
  visitIncompleteOrExpression(ctx: ParserRuleContext) {
    this.addClass(ctx, 'expression');
    this.visitChildren(ctx);
  }
  visitIncompleteAndExpression(ctx: ParserRuleContext) {
    this.addClass(ctx, 'expression');
    this.visitChildren(ctx);
  }
  visitParenthesizedExpression(ctx: ParenthesizedExpressionContext) {
    this.addActiveClass(ctx, 'active-parenthesis');
    this.visitChildren(ctx);
  }
  visitPostAttributeValueWhitespace(ctx: PostAttributeValueWhitespaceContext) {
    this.addClass(ctx, 'attribute-value-ws');
  }
}

export function applyStaticSyntaxHighlighting(cm: CodeMirror.Editor, errors: SyntaxError[]): void {
  const value = cm.getValue();

  // Clear existing marks to avoid duplication
  cm.getAllMarks().forEach((mark) => {
    mark.clear();
  });

  errors.forEach((error, idx) => {
    cm.markText(cm.posFromIndex(error.from), cm.posFromIndex(error.to), {
      className: `selection-input-error selection-input-error-${idx}`,
    });
  });

  const cursorIndex = cm.getCursor().ch;
  const {parseTrees} = parseInput(value);
  let start = 0;

  for (const {tree} of parseTrees) {
    const visitor = new SyntaxHighlightingVisitor(cm, start, cursorIndex - start);
    visitor.visit(tree);
    start += tree.text.length;
  }
  cm.markText(cm.posFromIndex(0), cm.posFromIndex(value.length), {className: 'selection'});

  requestAnimationFrame(() => {
    // Force CodeMirror to re-measure widths after applying CSS changes
    cm.refresh();
  });
}

export const SelectionAutoCompleteInputCSS = css`
  .CodeMirror:not(.CodeMirror-focused) {
    .CodeMirror-sizer,
    .CodeMirror-lines {
      height: 20px !important;
    }
  }
  .CodeMirror-sizer,
  .CodeMirror-lines {
    padding: 0;
  }
  width: 100%;
  ${TextInputStyles}
  flex-shrink: 1;
  overflow: auto;

  .CodeMirror-placeholder.CodeMirror-placeholder.CodeMirror-placeholder {
    color: ${Colors.textLighter()};
  }
  .CodeMirror-line > span {
    align-items: center;
  }

  .CodeMirror-scrollbar-filler,
  .CodeMirror-vscrollbar,
  .CodeMirror-hscrollbar {
    display: none !important;
  }

  .CodeMirror-cursor.CodeMirror-cursor {
    border-color: ${Colors.textLight()};
  }

  .CodeMirror {
    background: transparent;
    color: ${Colors.textDefault()};
    font-family: ${FontFamily.monospace};
  }

  .selection-input-error {
    background: unset;
    text-decoration-line: underline;
    text-decoration-style: wavy;
    text-decoration-color: ${Colors.accentRed()};
  }

  .expression {
    color: ${Colors.textGreen()};
  }

  .attribute-expression {
    color: ${Colors.textDefault()};
  }

  .attribute-name {
    color: ${Colors.textLighter()};
  }

  .value {
    color: ${Colors.textBlue()};
  }

  .function-name {
    color: ${Colors.textCyan()};
    font-style: italic;
  }

  .traversal {
    color: ${Colors.textRed()};
  }
`;
