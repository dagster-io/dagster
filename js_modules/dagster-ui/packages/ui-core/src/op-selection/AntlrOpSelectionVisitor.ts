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
    const expr = ctx.expr();
    return expr ? (this.visit(expr) ?? this.defaultResult()) : this.defaultResult();
  }

  visitTraversalAllowedExpression(ctx: TraversalAllowedExpressionContext) {
    const expr = ctx.traversalAllowedExpr();
    return expr ? (this.visit(expr) ?? this.defaultResult()) : this.defaultResult();
  }

  visitUpAndDownTraversalExpression(ctx: UpAndDownTraversalExpressionContext) {
    const traversalExpr = ctx.traversalAllowedExpr();
    const selection = traversalExpr
      ? (this.visit(traversalExpr) ?? this.defaultResult())
      : this.defaultResult();
    const upTraversal = ctx.upTraversal();
    const downTraversal = ctx.downTraversal();
    const up_depth = upTraversal ? getTraversalDepth(upTraversal) : 0;
    const down_depth = downTraversal ? getTraversalDepth(downTraversal) : 0;
    const selection_copy = new Set(selection);
    for (const item of selection_copy) {
      this.traverser.fetchUpstream(item, up_depth).forEach((i) => selection.add(i));
      this.traverser.fetchDownstream(item, down_depth).forEach((i) => selection.add(i));
    }
    return selection;
  }

  visitFunctionCallExpression(ctx: FunctionCallExpressionContext) {
    const funcName = ctx.functionName();
    const function_name = funcName ? getFunctionName(funcName) : '';
    const expr = ctx.expr();
    const selection = expr ? (this.visit(expr) ?? this.defaultResult()) : this.defaultResult();
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
    const traversalExpr = ctx.traversalAllowedExpr();
    const selection = traversalExpr
      ? (this.visit(traversalExpr) ?? this.defaultResult())
      : this.defaultResult();
    const upTraversal = ctx.upTraversal();
    const traversal_depth = upTraversal ? getTraversalDepth(upTraversal) : 0;
    const selection_copy = new Set(selection);
    for (const item of selection_copy) {
      this.traverser.fetchUpstream(item, traversal_depth).forEach((i) => selection.add(i));
    }
    return selection;
  }

  visitDownTraversalExpression(ctx: DownTraversalExpressionContext) {
    const traversalExpr = ctx.traversalAllowedExpr();
    const selection = traversalExpr
      ? (this.visit(traversalExpr) ?? this.defaultResult())
      : this.defaultResult();
    const downTraversal = ctx.downTraversal();
    const traversal_depth = downTraversal ? getTraversalDepth(downTraversal) : 0;
    const selection_copy = new Set(selection);
    for (const item of selection_copy) {
      this.traverser.fetchDownstream(item, traversal_depth).forEach((i) => selection.add(i));
    }
    return selection;
  }

  visitNotExpression(ctx: NotExpressionContext) {
    const expr = ctx.expr();
    const selection = expr ? (this.visit(expr) ?? this.defaultResult()) : this.defaultResult();
    return new Set([...this.all_ops].filter((i) => !selection.has(i)));
  }

  visitAndExpression(ctx: AndExpressionContext) {
    const leftExpr = ctx.expr(0);
    const rightExpr = ctx.expr(1);
    const left = leftExpr ? (this.visit(leftExpr) ?? this.defaultResult()) : this.defaultResult();
    const right = rightExpr
      ? (this.visit(rightExpr) ?? this.defaultResult())
      : this.defaultResult();
    return new Set([...left].filter((i) => right.has(i)));
  }

  visitOrExpression(ctx: OrExpressionContext) {
    const leftExpr = ctx.expr(0);
    const rightExpr = ctx.expr(1);
    const left = leftExpr ? (this.visit(leftExpr) ?? this.defaultResult()) : this.defaultResult();
    const right = rightExpr
      ? (this.visit(rightExpr) ?? this.defaultResult())
      : this.defaultResult();
    return new Set([...left, ...right]);
  }

  visitAllExpression(_ctx: AllExpressionContext) {
    return this.all_ops;
  }

  visitAttributeExpression(ctx: AttributeExpressionContext) {
    const attrExpr = ctx.attributeExpr();
    return attrExpr ? (this.visit(attrExpr) ?? this.defaultResult()) : this.defaultResult();
  }

  visitParenthesizedExpression(ctx: ParenthesizedExpressionContext) {
    const expr = ctx.expr();
    return expr ? (this.visit(expr) ?? this.defaultResult()) : this.defaultResult();
  }

  visitNameExpr(ctx: NameExprContext) {
    const keyValue = ctx.keyValue();
    const value = keyValue ? getValue(keyValue) : '';
    const regex: RegExp = new RegExp(`^${escapeRegExp(value).replaceAll('\\*', '.*')}$`);
    const selection = [...this.all_ops].filter((i) => regex.test(i.name));
    selection.forEach((i) => this.focus_ops.add(i));
    return new Set(selection);
  }
}
