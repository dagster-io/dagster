import {AbstractParseTreeVisitor} from 'antlr4ts/tree/AbstractParseTreeVisitor';

import {
  AllExpressionContext,
  AndExpressionContext,
  AttributeExpressionContext,
  CodeLocationAttributeExprContext,
  DownTraversalContext,
  DownTraversalExpressionContext,
  FunctionCallExpressionContext,
  FunctionNameContext,
  GroupAttributeExprContext,
  KeyExprContext,
  KeySubstringExprContext,
  KindAttributeExprContext,
  NotExpressionContext,
  OrExpressionContext,
  OwnerAttributeExprContext,
  ParenthesizedExpressionContext,
  StartContext,
  TagAttributeExprContext,
  TraversalAllowedExpressionContext,
  UpAndDownTraversalExpressionContext,
  UpTraversalContext,
  UpTraversalExpressionContext,
  ValueContext,
} from './generated/AssetSelectionParser';
import {AssetSelectionVisitor} from './generated/AssetSelectionVisitor';
import {GraphTraverser} from '../app/GraphQueryImpl';
import {AssetGraphQueryItem} from '../asset-graph/useAssetGraphData';
import {buildRepoPathForHuman} from '../workspace/buildRepoAddress';

export function getTraversalDepth(ctx: UpTraversalContext | DownTraversalContext): number {
  const digits = ctx.DIGITS();
  if (digits) {
    return parseInt(ctx.text);
  }
  return Number.MAX_SAFE_INTEGER;
}

export function getFunctionName(ctx: FunctionNameContext): string {
  if (ctx.SINKS()) {
    return 'sinks';
  }
  if (ctx.ROOTS()) {
    return 'roots';
  }
  throw new Error('Invalid function name');
}

export function getValue(ctx: ValueContext): string {
  if (ctx.QUOTED_STRING()) {
    return ctx.text.slice(1, -1);
  }
  if (ctx.UNQUOTED_STRING()) {
    return ctx.text;
  }
  throw new Error('Invalid value');
}

export class AntlrAssetSelectionVisitor
  extends AbstractParseTreeVisitor<Set<AssetGraphQueryItem>>
  implements AssetSelectionVisitor<Set<AssetGraphQueryItem>>
{
  all_assets: Set<AssetGraphQueryItem>;
  focus_assets: Set<AssetGraphQueryItem>;
  traverser: GraphTraverser<AssetGraphQueryItem>;

  protected defaultResult() {
    return new Set<AssetGraphQueryItem>();
  }

  constructor(all_assets: AssetGraphQueryItem[]) {
    super();
    this.all_assets = new Set(all_assets);
    this.focus_assets = new Set();
    this.traverser = new GraphTraverser(all_assets);
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
    return new Set([...this.all_assets].filter((i) => !selection.has(i)));
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
    return this.all_assets;
  }

  visitAttributeExpression(ctx: AttributeExpressionContext) {
    return this.visit(ctx.attributeExpr());
  }

  visitFunctionCallExpression(ctx: FunctionCallExpressionContext) {
    const function_name: string = getFunctionName(ctx.functionName());
    const selection = this.visit(ctx.expr());
    if (function_name === 'sinks') {
      const sinks = new Set<AssetGraphQueryItem>();
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
      const roots = new Set<AssetGraphQueryItem>();
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

  visitKeyExpr(ctx: KeyExprContext) {
    const value: string = getValue(ctx.value());
    const selection = [...this.all_assets].filter((i) => i.name === value);
    selection.forEach((i) => this.focus_assets.add(i));
    return new Set(selection);
  }

  visitKeySubstringExpr(ctx: KeySubstringExprContext) {
    const value: string = getValue(ctx.value());
    const selection = [...this.all_assets].filter((i) => i.name.includes(value));
    selection.forEach((i) => this.focus_assets.add(i));
    return new Set(selection);
  }

  visitTagAttributeExpr(ctx: TagAttributeExprContext) {
    const key: string = getValue(ctx.value(0));
    if (ctx.EQUAL()) {
      const value: string = getValue(ctx.value(1));
      return new Set(
        [...this.all_assets].filter((i) =>
          i.node.tags.some((t) => t.key === key && t.value === value),
        ),
      );
    }
    return new Set([...this.all_assets].filter((i) => i.node.tags.some((t) => t.key === key)));
  }

  visitOwnerAttributeExpr(ctx: OwnerAttributeExprContext) {
    const value: string = getValue(ctx.value());
    return new Set(
      [...this.all_assets].filter((i) =>
        i.node.owners.some((o) => {
          if (o.__typename === 'TeamAssetOwner') {
            return o.team === value;
          } else {
            return o.email === value;
          }
        }),
      ),
    );
  }

  visitGroupAttributeExpr(ctx: GroupAttributeExprContext) {
    const value: string = getValue(ctx.value());
    return new Set([...this.all_assets].filter((i) => i.node.groupName === value));
  }

  visitKindAttributeExpr(ctx: KindAttributeExprContext) {
    const value: string = getValue(ctx.value());
    return new Set([...this.all_assets].filter((i) => i.node.kinds.some((k) => k === value)));
  }

  visitCodeLocationAttributeExpr(ctx: CodeLocationAttributeExprContext) {
    const value: string = getValue(ctx.value());
    const selection = new Set<AssetGraphQueryItem>();
    for (const asset of this.all_assets) {
      const location = buildRepoPathForHuman(
        asset.node.repository.name,
        asset.node.repository.location.name,
      );
      if (location === value) {
        selection.add(asset);
      }
    }
    return selection;
  }
}
