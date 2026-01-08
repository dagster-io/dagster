import {AbstractParseTreeVisitor} from 'antlr4ng';
import escapeRegExp from 'lodash/escapeRegExp';

import {GraphQueryItem, GraphTraverser} from '../app/GraphQueryImpl';
import {
  AllExpressionContext,
  AndExpressionContext,
  AttributeExpressionContext,
  DownTraversalExpressionContext,
  FunctionCallExpressionContext,
  NameExprContext,
  NotExpressionContext,
  OrExpressionContext,
  ParenthesizedExpressionContext,
  StartContext,
  TraversalAllowedExpressionContext,
  UpAndDownTraversalExpressionContext,
  UpTraversalExpressionContext,
} from './generated/OpSelectionParser';
import {OpSelectionVisitor} from './generated/OpSelectionVisitor';
import {getFunctionName, getTraversalDepth, getValue} from '../asset-selection/util';
export class AntlrOpSelectionVisitor<T extends GraphQueryItem>
  extends AbstractParseTreeVisitor<Set<T>>
  implements OpSelectionVisitor<Set<T>>
{
  all_ops: Set<T>;
  focus_ops: Set<T>;
  traverser: GraphTraverser<T>;

  protected defaultResult() {
    return new Set<T>();
  }

  constructor(all_ops: T[]) {
    super();
    this.all_ops = new Set(all_ops);
    this.focus_ops = new Set();
    this.traverser = new GraphTraverser(all_ops);
  }

  visitStart(ctx: StartContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    return this.visit(ctx.expr()!) ?? this.defaultResult();
  }

  visitTraversalAllowedExpression(ctx: TraversalAllowedExpressionContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    return this.visit(ctx.traversalAllowedExpr()!) ?? this.defaultResult();
  }

  visitUpAndDownTraversalExpression(ctx: UpAndDownTraversalExpressionContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const selection = this.visit(ctx.traversalAllowedExpr()!) ?? this.defaultResult();
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const up_depth: number = getTraversalDepth(ctx.upTraversal()!);
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const down_depth: number = getTraversalDepth(ctx.downTraversal()!);
    const selection_copy = new Set(selection);
    for (const item of selection_copy) {
      this.traverser.fetchUpstream(item, up_depth).forEach((i) => selection.add(i));
      this.traverser.fetchDownstream(item, down_depth).forEach((i) => selection.add(i));
    }
    return selection;
  }

  visitFunctionCallExpression(ctx: FunctionCallExpressionContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const function_name: string = getFunctionName(ctx.functionName()!);
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const selection = this.visit(ctx.expr()!) ?? this.defaultResult();
    if (function_name === 'sinks') {
      const sinks = new Set<T>();
      for (const item of selection) {
        const downstream = this.traverser
          .fetchDownstream(item, Number.MAX_VALUE)
          .filter((i) => selection.has(i));
        if (downstream.length === 0 || (downstream.length === 1 && downstream[0] === item)) {
          sinks.add(item);
        }
      }
      return sinks;
    }
    if (function_name === 'roots') {
      const roots = new Set<T>();
      for (const item of selection) {
        const upstream = this.traverser
          .fetchUpstream(item, Number.MAX_VALUE)
          .filter((i) => selection.has(i));
        if (upstream.length === 0 || (upstream.length === 1 && upstream[0] === item)) {
          roots.add(item);
        }
      }
      return roots;
    }
    throw new Error(`Unknown function: ${function_name}`);
  }

  visitUpTraversalExpression(ctx: UpTraversalExpressionContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const selection = this.visit(ctx.traversalAllowedExpr()!) ?? this.defaultResult();
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const traversal_depth: number = getTraversalDepth(ctx.upTraversal()!);
    const selection_copy = new Set(selection);
    for (const item of selection_copy) {
      this.traverser.fetchUpstream(item, traversal_depth).forEach((i) => selection.add(i));
    }
    return selection;
  }

  visitDownTraversalExpression(ctx: DownTraversalExpressionContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const selection = this.visit(ctx.traversalAllowedExpr()!) ?? this.defaultResult();
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const traversal_depth: number = getTraversalDepth(ctx.downTraversal()!);
    const selection_copy = new Set(selection);
    for (const item of selection_copy) {
      this.traverser.fetchDownstream(item, traversal_depth).forEach((i) => selection.add(i));
    }
    return selection;
  }

  visitNotExpression(ctx: NotExpressionContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const selection = this.visit(ctx.expr()!) ?? this.defaultResult();
    return new Set([...this.all_ops].filter((i) => !selection.has(i)));
  }

  visitAndExpression(ctx: AndExpressionContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const left = this.visit(ctx.expr(0)!) ?? this.defaultResult();
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const right = this.visit(ctx.expr(1)!) ?? this.defaultResult();
    return new Set([...left].filter((i) => right.has(i)));
  }

  visitOrExpression(ctx: OrExpressionContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const left = this.visit(ctx.expr(0)!) ?? this.defaultResult();
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const right = this.visit(ctx.expr(1)!) ?? this.defaultResult();
    return new Set([...left, ...right]);
  }

  visitAllExpression(_ctx: AllExpressionContext) {
    return this.all_ops;
  }

  visitAttributeExpression(ctx: AttributeExpressionContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    return this.visit(ctx.attributeExpr()!) ?? this.defaultResult();
  }

  visitParenthesizedExpression(ctx: ParenthesizedExpressionContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    return this.visit(ctx.expr()!) ?? this.defaultResult();
  }

  visitNameExpr(ctx: NameExprContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const value: string = getValue(ctx.keyValue()!);
    const regex: RegExp = new RegExp(`^${escapeRegExp(value).replaceAll('\\*', '.*')}$`);
    const selection = [...this.all_ops].filter((i) => regex.test(i.name));
    selection.forEach((i) => this.focus_ops.add(i));
    return new Set(selection);
  }
}
