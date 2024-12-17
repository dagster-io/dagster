import {AbstractParseTreeVisitor} from 'antlr4ts/tree/AbstractParseTreeVisitor';

import {GraphQueryItem, GraphTraverser} from '../app/GraphQueryImpl';
import {
  AllExpressionContext,
  AndExpressionContext,
  AttributeExpressionContext,
  DownTraversalExpressionContext,
  NameExprContext,
  NameSubstringExprContext,
  NotExpressionContext,
  OrExpressionContext,
  ParenthesizedExpressionContext,
  StartContext,
  TraversalAllowedExpressionContext,
  UpAndDownTraversalExpressionContext,
  UpTraversalExpressionContext,
} from './generated/OpSelectionParser';
import {OpSelectionVisitor} from './generated/OpSelectionVisitor';
import {getTraversalDepth, getValue} from '../asset-selection/AntlrAssetSelectionVisitor';

export class AntlrOpSelectionVisitor
  extends AbstractParseTreeVisitor<Set<GraphQueryItem>>
  implements OpSelectionVisitor<Set<GraphQueryItem>>
{
  all_ops: Set<GraphQueryItem>;
  focus_ops: Set<GraphQueryItem>;
  traverser: GraphTraverser<GraphQueryItem>;

  protected defaultResult() {
    return new Set<GraphQueryItem>();
  }

  constructor(all_ops: GraphQueryItem[]) {
    super();
    this.all_ops = new Set(all_ops);
    this.focus_ops = new Set();
    this.traverser = new GraphTraverser(all_ops);
  }

  visitStart(ctx: StartContext) {
    return this.visit(ctx.expr());
  }

  visitTraversalAllowedExpression(ctx: TraversalAllowedExpressionContext) {
    return this.visit(ctx.traversalAllowedExpr());
  }

  visitUpAndDownTraversalExpression(ctx: UpAndDownTraversalExpressionContext) {
    const selection = this.visit(ctx.traversalAllowedExpr());
    const up_depth: number = getTraversalDepth(ctx.traversal(0));
    const down_depth: number = getTraversalDepth(ctx.traversal(1));
    const selection_copy = new Set(selection);
    for (const item of selection_copy) {
      this.traverser.fetchUpstream(item, up_depth).forEach((i) => selection.add(i));
      this.traverser.fetchDownstream(item, down_depth).forEach((i) => selection.add(i));
    }
    return selection;
  }

  visitUpTraversalExpression(ctx: UpTraversalExpressionContext) {
    const selection = this.visit(ctx.traversalAllowedExpr());
    const traversal_depth: number = getTraversalDepth(ctx.traversal());
    const selection_copy = new Set(selection);
    for (const item of selection_copy) {
      this.traverser.fetchUpstream(item, traversal_depth).forEach((i) => selection.add(i));
    }
    return selection;
  }

  visitDownTraversalExpression(ctx: DownTraversalExpressionContext) {
    const selection = this.visit(ctx.traversalAllowedExpr());
    const traversal_depth: number = getTraversalDepth(ctx.traversal());
    const selection_copy = new Set(selection);
    for (const item of selection_copy) {
      this.traverser.fetchDownstream(item, traversal_depth).forEach((i) => selection.add(i));
    }
    return selection;
  }

  visitNotExpression(ctx: NotExpressionContext) {
    const selection = this.visit(ctx.expr());
    return new Set([...this.all_ops].filter((i) => !selection.has(i)));
  }

  visitAndExpression(ctx: AndExpressionContext) {
    const left = this.visit(ctx.expr(0));
    const right = this.visit(ctx.expr(1));
    return new Set([...left].filter((i) => right.has(i)));
  }

  visitOrExpression(ctx: OrExpressionContext) {
    const left = this.visit(ctx.expr(0));
    const right = this.visit(ctx.expr(1));
    return new Set([...left, ...right]);
  }

  visitAllExpression(_ctx: AllExpressionContext) {
    return this.all_ops;
  }

  visitAttributeExpression(ctx: AttributeExpressionContext) {
    return this.visit(ctx.attributeExpr());
  }

  visitParenthesizedExpression(ctx: ParenthesizedExpressionContext) {
    return this.visit(ctx.expr());
  }

  visitNameExpr(ctx: NameExprContext) {
    const value: string = getValue(ctx.value());
    const selection = [...this.all_ops].filter((i) => i.name === value);
    selection.forEach((i) => this.focus_ops.add(i));
    return new Set(selection);
  }

  visitNameSubstringExpr(ctx: NameSubstringExprContext) {
    const value: string = getValue(ctx.value());
    const selection = [...this.all_ops].filter((i) => i.name.includes(value));
    selection.forEach((i) => this.focus_ops.add(i));
    return new Set(selection);
  }
}
