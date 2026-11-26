import {TerminalNode} from 'antlr4ng';

import {BaseSelectionVisitor} from '../../selection/BaseSelectionVisitor';
import {getParseTreeAtCursor} from '../../selection/SelectionInputParser';
import {getValueNodeValue} from '../../selection/SelectionInputUtil';
import {
  AttributeExpressionContext,
  AttributeValueContext,
  IncompleteAttributeExpressionMissingSecondValueContext,
  IncompleteNotExpressionContext,
  NotExpressionContext,
} from '../../selection/generated/SelectionAutoCompleteParser';

type RunsSearchContextAtCursor = {
  /** The key of the pair whose value the cursor is in or right after. */
  valueKey: string | null;
  /** Where a key row's replacement ends: just past the `=`. */
  keyRangeEnd: number | null;
  /** Whether the key the cursor is on was typed in quotes. */
  keyQuoted: boolean;
  isNegated: boolean;
};

class RunsSearchContextVisitor extends BaseSelectionVisitor {
  public valueKey: string | null = null;
  public keyRangeEnd: number | null = null;
  public keyQuoted = false;
  public isNegated = false;

  public visitNotExpression(ctx: NotExpressionContext) {
    this.visitNegation(ctx);
  }

  public visitIncompleteNotExpression(ctx: IncompleteNotExpressionContext) {
    this.visitNegation(ctx);
  }

  private visitNegation(ctx: IncompleteNotExpressionContext | NotExpressionContext) {
    const notEnd = (ctx.notToken().stop?.stop ?? 0) + 1;
    if (this.cursorIndex >= notEnd) {
      this.isNegated = true;
    }
    this.visitChildren(ctx);
  }

  private isCursorOn(ctx: AttributeValueContext) {
    const start = ctx.start?.start ?? 0;
    const end = (ctx.stop?.stop ?? 0) + 1;
    return this.cursorIndex >= start && this.cursorIndex <= end;
  }

  private visitKey(keyCtx: AttributeValueContext | null, equal: TerminalNode | null) {
    if (!keyCtx || !this.isCursorOn(keyCtx)) {
      return;
    }

    this.keyQuoted = keyCtx.getText().startsWith('"');

    // Past a closing quote the shared visitor offers `and`/`or`, not the key, so keep its range.
    const keyEnd = (keyCtx.stop?.stop ?? 0) + 1;
    const isAfterClosingQuote = this.cursorIndex === keyEnd && this.line[keyEnd - 1] === '"';
    if (equal && !isAfterClosingQuote) {
      this.keyRangeEnd = equal.symbol.stop + 1;
    }
  }

  public visitAttributeExpression(ctx: AttributeExpressionContext) {
    if (ctx.attributeName().getText() !== 'tag') {
      return;
    }

    this.visitKey(ctx.attributeValue(0), ctx.EQUAL());

    const valueCtx = ctx.attributeValue(1);
    if (valueCtx && this.isCursorOn(valueCtx)) {
      this.valueKey = getValueNodeValue(ctx.attributeValue(0));
    }
  }

  public visitIncompleteAttributeExpressionMissingSecondValue(
    ctx: IncompleteAttributeExpressionMissingSecondValueContext,
  ) {
    if (ctx.attributeName().getText() !== 'tag') {
      return;
    }

    this.visitKey(ctx.attributeValue(), ctx.EQUAL());

    if (this.cursorIndex > ctx.EQUAL().symbol.start) {
      this.valueKey = getValueNodeValue(ctx.attributeValue());
    }
  }
}

/** The negation and tag pair, if any, that contain the cursor. */
export const getRunsSearchContextAtCursor = (
  line: string,
  cursorIndex: number,
): RunsSearchContextAtCursor => {
  const treeAtCursor = getParseTreeAtCursor(line, cursorIndex);
  if (!treeAtCursor) {
    return {
      valueKey: null,
      keyRangeEnd: null,
      keyQuoted: false,
      isNegated: false,
    };
  }

  const visitor = new RunsSearchContextVisitor({
    line: treeAtCursor.line,
    cursorIndex: cursorIndex - treeAtCursor.startOffset,
  });
  treeAtCursor.tree.accept(visitor);

  return {
    valueKey: visitor.valueKey || null,
    keyRangeEnd:
      visitor.keyRangeEnd !== null ? treeAtCursor.startOffset + visitor.keyRangeEnd : null,
    keyQuoted: visitor.keyQuoted,
    isNegated: visitor.isNegated,
  };
};
