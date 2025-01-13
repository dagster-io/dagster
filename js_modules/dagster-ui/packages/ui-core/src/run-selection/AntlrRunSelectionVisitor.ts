import {AbstractParseTreeVisitor} from 'antlr4ts/tree/AbstractParseTreeVisitor';

import {GraphTraverser} from '../app/GraphQueryImpl';
import {RunGraphQueryItem} from '../gantt/toGraphQueryItems';
import {
  AllExpressionContext,
  AndExpressionContext,
  AttributeExpressionContext,
  DownTraversalExpressionContext,
  FunctionCallExpressionContext,
  NameExprContext,
  NameSubstringExprContext,
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
import {
  getFunctionName,
  getTraversalDepth,
  getValue,
} from '../asset-selection/AntlrAssetSelectionVisitor';

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
    return this.visit(ctx.expr());
  }

  visitTraversalAllowedExpression(ctx: TraversalAllowedExpressionContext) {
    return this.visit(ctx.traversalAllowedExpr());
  }

  visitUpAndDownTraversalExpression(ctx: UpAndDownTraversalExpressionContext) {
    const selection = this.visit(ctx.traversalAllowedExpr());
    const up_depth: number = getTraversalDepth(ctx.upTraversal());
    const down_depth: number = getTraversalDepth(ctx.downTraversal());
    const selection_copy = new Set(selection);
    for (const item of selection_copy) {
      this.traverser.fetchUpstream(item, up_depth).forEach((i) => selection.add(i));
      this.traverser.fetchDownstream(item, down_depth).forEach((i) => selection.add(i));
    }
    return selection;
  }

  visitUpTraversalExpression(ctx: UpTraversalExpressionContext) {
    const selection = this.visit(ctx.traversalAllowedExpr());
    const traversal_depth: number = getTraversalDepth(ctx.upTraversal());
    const selection_copy = new Set(selection);
    for (const item of selection_copy) {
      this.traverser.fetchUpstream(item, traversal_depth).forEach((i) => selection.add(i));
    }
    return selection;
  }

  visitDownTraversalExpression(ctx: DownTraversalExpressionContext) {
    const selection = this.visit(ctx.traversalAllowedExpr());
    const traversal_depth: number = getTraversalDepth(ctx.downTraversal());
    const selection_copy = new Set(selection);
    for (const item of selection_copy) {
      this.traverser.fetchDownstream(item, traversal_depth).forEach((i) => selection.add(i));
    }
    return selection;
  }

  visitNotExpression(ctx: NotExpressionContext) {
    const selection = this.visit(ctx.expr());
    return new Set([...this.all_runs].filter((i) => !selection.has(i)));
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
    return this.all_runs;
  }

  visitAttributeExpression(ctx: AttributeExpressionContext) {
    return this.visit(ctx.attributeExpr());
  }

  visitFunctionCallExpression(ctx: FunctionCallExpressionContext) {
    const function_name: string = getFunctionName(ctx.functionName());
    const selection = this.visit(ctx.expr());
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
    return this.visit(ctx.expr());
  }

  visitNameExpr(ctx: NameExprContext) {
    const value: string = getValue(ctx.value());
    const selection = [...this.all_runs].filter((i) => i.name === value);
    selection.forEach((i) => this.focus_runs.add(i));
    return new Set(selection);
  }

  visitNameSubstringExpr(ctx: NameSubstringExprContext) {
    const value: string = getValue(ctx.value());
    const selection = [...this.all_runs].filter((i) => i.name.includes(value));
    selection.forEach((i) => this.focus_runs.add(i));
    return new Set(selection);
  }

  visitStatusAttributeExpr(ctx: StatusAttributeExprContext) {
    const state: string = getValue(ctx.value()).toLowerCase();
    return new Set(
      [...this.all_runs].filter(
        (i) => i.metadata?.state === state || (state === NO_STATE && !i.metadata?.state),
      ),
    );
  }
}

export const NO_STATE = 'none';
