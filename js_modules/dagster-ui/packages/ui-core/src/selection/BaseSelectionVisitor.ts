import {ParserRuleContext} from 'antlr4ts';
import {AbstractParseTreeVisitor} from 'antlr4ts/tree/AbstractParseTreeVisitor';
import {ParseTree} from 'antlr4ts/tree/ParseTree';
import {RuleNode} from 'antlr4ts/tree/RuleNode';

import {
  ParenthesizedExpressionContext,
  PostAttributeValueWhitespaceContext,
} from './generated/SelectionAutoCompleteParser';
import {SelectionAutoCompleteVisitor as _SelectionAutoCompleteVisitor} from './generated/SelectionAutoCompleteVisitor';

/**
 * A base visitor that handles logic for:
 * - Deciding whether the current cursor is inside a node (and thus whether to visit it),
 * - The forced-visit (`forceVisit`) mechanism,
 * - The standard tree walking logic (`visit`, `visitChildren`).
 *
 * Subclasses can override individual visitXyz() methods to implement their own behavior
 * (e.g. collecting suggestions, triggering async lookups, etc.).
 */
export class BaseSelectionVisitor
  extends AbstractParseTreeVisitor<void>
  implements _SelectionAutoCompleteVisitor<void>
{
  protected cursorIndex: number;
  protected line: string;
  protected forceVisitCtx = new WeakSet<ParserRuleContext>();

  constructor({line, cursorIndex}: {line: string; cursorIndex: number}) {
    super();
    this.line = line;
    this.cursorIndex = cursorIndex;
  }

  /**
   * Force visiting a context even if the usual cursor-based logic would skip it.
   */
  protected forceVisit(ctx: ParserRuleContext) {
    this.forceVisitCtx.add(ctx);
    ctx.accept(this);
  }

  /**
   * Visit a node, but only if the node includes the cursor position OR we are forced to visit it.
   */
  public visit(tree: ParseTree) {
    const ruleContext = tree as ParserRuleContext;
    if (
      ruleContext.start.startIndex !== undefined &&
      ruleContext.stop?.stopIndex !== undefined &&
      !this.nodeIncludesCursor(ruleContext) &&
      !this.forceVisitCtx.has(ruleContext)
    ) {
      // If not forced and the cursor is not inside, skip visiting children.
      // (Optionally handle top-level whitespace if needed)
      if (!tree.parent) {
        // If we're at the root but not within the expression then
        // derived classes can handle "empty input" logic if desired.
        this.handleCursorOutsideAnyNode();
      }
      return;
    }
    return super.visit(tree);
  }

  /**
   * Visit children, but only those that include the cursor or are forced.
   */
  public visitChildren(node: RuleNode) {
    let result = this.defaultResult();

    const childCount = node.childCount;
    for (let i = 0; i < childCount; i++) {
      if (!this.shouldVisitNextChild(node, result)) {
        break;
      }
      const child = node.getChild(i) as ParserRuleContext;

      // If child's start..stop doesn't include the cursor, skip
      // (unless forced)
      if (child.start && child.stop) {
        const isWhitespace = child.constructor.name.endsWith('WhitespaceContext');
        if (
          !this.nodeIncludesCursor(child) &&
          (!isWhitespace || child.start.startIndex !== this.cursorIndex) &&
          !this.forceVisitCtx.has(child)
        ) {
          continue;
        }
        // If next child is whitespace and we aren't forced, skip, etc...
        const nextChild = i + 1 < childCount ? (node.getChild(i + 1) as ParserRuleContext) : null;
        if (
          !this.nodeIncludesCursor(child, 0) &&
          nextChild?.constructor.name.endsWith('WhitespaceContext') &&
          !this.forceVisitCtx.has(child)
        ) {
          continue;
        }
      }

      const childResult = child.accept(this);
      result = this.aggregateResult(result, childResult);
    }

    return result;
  }

  /**
   * By default, do nothing for the tree-walking return value.
   */
  protected defaultResult() {
    return;
  }

  /**
   * Utility to see if the visitor's cursorIndex is within a given context's range.
   */
  protected nodeIncludesCursor(
    ctx: Pick<ParserRuleContext, 'start' | 'stop'>,
    modifier: number = -1,
  ): boolean {
    const start = ctx.start.startIndex;
    const stop = ctx.stop ? ctx.stop.stopIndex : ctx.start.startIndex;
    // If the parser did not produce a .stopIndex, fallback to just start
    const effCursor = Math.max(0, this.cursorIndex + modifier);

    return effCursor >= start && effCursor <= stop;
  }

  public visitPostAttributeValueWhitespace(ctx: PostAttributeValueWhitespaceContext) {
    const attributeValue = ctx.parent!.getChild(2) as ParserRuleContext;
    if (this.cursorIndex === (attributeValue?.stop?.stopIndex ?? 0) + 1) {
      this.forceVisit(attributeValue);
    } else {
      this.visitPostExpressionWhitespace(ctx);
    }
  }

  public visitParenthesizedExpression(ctx: ParenthesizedExpressionContext) {
    if (this.nodeIncludesCursor(ctx.leftParenToken())) {
      // Move the cursor to the right and visit that expression.
      this.cursorIndex += 1;
    }
    this.visitChildren(ctx);
  }

  /**
   * Hook for derived classes to handle the scenario "cursor is outside any expression."
   * E.g. you might want to show "all possible suggestions" or do nothing.
   */
  protected handleCursorOutsideAnyNode(): void {
    // no-op by default
  }

  // --------------------------------------------------------------------------
  // The methods below correspond to parser rules. By default, do nothing,
  // so that derived classes can selectively override them if they want
  // to handle specific logic for each node type.
  // --------------------------------------------------------------------------

  public visitAllExpression(_ctx: any) {
    // no-op in the base visitor
  }

  public visitUpTraversal(_ctx: any) {
    // no-op
  }

  public visitDownTraversal(_ctx: any) {
    // no-op
  }

  public visitFunctionName(_ctx: any) {
    // no-op
  }

  public visitAttributeValue(_ctx: any) {
    // no-op
  }

  public visitColonToken(_ctx: any) {
    // no-op
  }

  public visitAttributeName(_ctx: any) {
    // no-op
  }

  public visitOrToken(_ctx: any) {
    // no-op
  }

  public visitAndToken(_ctx: any) {
    // no-op
  }

  public visitUnmatchedValue(_ctx: any) {
    // no-op
  }

  public visitIncompletePlusTraversalExpression(_ctx: any) {
    // no-op
  }

  public visitIncompleteAttributeExpressionMissingValue(_ctx: any) {
    // no-op
  }

  public visitPostNotOperatorWhitespace(_ctx: any) {
    // no-op
  }

  public visitPostNeighborTraversalWhitespace(_ctx: any) {
    // no-op
  }

  public visitPostUpwardTraversalWhitespace(_ctx: any) {
    // no-op
  }

  public visitPostDownwardTraversalWhitespace(_ctx: any) {
    // no-op
  }

  public visitPostExpressionWhitespace(_ctx: any) {
    // no-op
  }

  public visitPostLogicalOperatorWhitespace(_ctx: any) {
    // no-op
  }
}
