import {AbstractParseTreeVisitor} from 'antlr4ng';
import escapeRegExp from 'lodash/escapeRegExp';

import {GraphTraverser} from '../app/GraphQueryImpl';
import {RunGraphQueryItem} from '../gantt/toGraphQueryItems';
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
  StatusAttributeExprContext,
  TraversalAllowedExpressionContext,
  UpAndDownTraversalExpressionContext,
  UpTraversalExpressionContext,
} from './generated/RunSelectionParser';
import {RunSelectionVisitor} from './generated/RunSelectionVisitor';
import {getFunctionName, getTraversalDepth, getValue} from '../asset-selection/util';
export class AntlrRunSelectionVisitor
  extends AbstractParseTreeVisitor<Set<RunGraphQueryItem>>
  implements RunSelectionVisitor<Set<RunGraphQueryItem>>
{
  all_runs: Set<RunGraphQueryItem>;
  focus_runs: Set<RunGraphQueryItem>;
  traverser: GraphTraverser<RunGraphQueryItem>;

  protected defaultResult() {
    return new Set<RunGraphQueryItem>();
  }

  constructor(all_runs: RunGraphQueryItem[]) {
    super();
    this.all_runs = new Set(all_runs);
    this.focus_runs = new Set();
    this.traverser = new GraphTraverser(all_runs);
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
    return new Set([...this.all_runs].filter((i) => !selection.has(i)));
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
    return this.all_runs;
  }

  visitAttributeExpression(ctx: AttributeExpressionContext) {
    const attrExpr = ctx.attributeExpr();
    return attrExpr ? (this.visit(attrExpr) ?? this.defaultResult()) : this.defaultResult();
  }

  visitFunctionCallExpression(ctx: FunctionCallExpressionContext) {
    const funcName = ctx.functionName();
    const function_name = funcName ? getFunctionName(funcName) : '';
    const expr = ctx.expr();
    const selection = expr ? (this.visit(expr) ?? this.defaultResult()) : this.defaultResult();
    if (function_name === 'sinks') {
      const sinks = new Set<RunGraphQueryItem>();
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
      const roots = new Set<RunGraphQueryItem>();
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

  visitParenthesizedExpression(ctx: ParenthesizedExpressionContext) {
    const expr = ctx.expr();
    return expr ? (this.visit(expr) ?? this.defaultResult()) : this.defaultResult();
  }

  visitNameExpr(ctx: NameExprContext) {
    const keyValue = ctx.keyValue();
    const value = keyValue ? getValue(keyValue) : '';
    const regex: RegExp = new RegExp(`^${escapeRegExp(value).replaceAll('\\*', '.*')}$`);
    const selection = [...this.all_runs].filter((i) => regex.test(i.name));
    selection.forEach((i) => this.focus_runs.add(i));
    return new Set(selection);
  }

  visitStatusAttributeExpr(ctx: StatusAttributeExprContext) {
    const valueCtx = ctx.value();
    const state = valueCtx ? getValue(valueCtx).toLowerCase() : '';
    return new Set(
      [...this.all_runs].filter(
        (i) => i.metadata?.state === state || (state === NO_STATE && !i.metadata?.state),
      ),
    );
  }
}

export const NO_STATE = 'none';
