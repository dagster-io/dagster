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
    return new Set([...this.all_runs].filter((i) => !selection.has(i)));
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
    return this.all_runs;
  }

  visitAttributeExpression(ctx: AttributeExpressionContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    return this.visit(ctx.attributeExpr()!) ?? this.defaultResult();
  }

  visitFunctionCallExpression(ctx: FunctionCallExpressionContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const function_name: string = getFunctionName(ctx.functionName()!);
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const selection = this.visit(ctx.expr()!) ?? this.defaultResult();
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
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    return this.visit(ctx.expr()!) ?? this.defaultResult();
  }

  visitNameExpr(ctx: NameExprContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const value: string = getValue(ctx.keyValue()!);
    const regex: RegExp = new RegExp(`^${escapeRegExp(value).replaceAll('\\*', '.*')}$`);
    const selection = [...this.all_runs].filter((i) => regex.test(i.name));
    selection.forEach((i) => this.focus_runs.add(i));
    return new Set(selection);
  }

  visitStatusAttributeExpr(ctx: StatusAttributeExprContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const state: string = getValue(ctx.value()!).toLowerCase();
    return new Set(
      [...this.all_runs].filter(
        (i) => i.metadata?.state === state || (state === NO_STATE && !i.metadata?.state),
      ),
    );
  }
}

export const NO_STATE = 'none';
