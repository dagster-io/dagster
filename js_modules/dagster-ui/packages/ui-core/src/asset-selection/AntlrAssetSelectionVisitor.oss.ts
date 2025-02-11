import {AbstractParseTreeVisitor} from 'antlr4ts/tree/AbstractParseTreeVisitor';
import {SupplementaryInformation} from 'shared/asset-graph/useAssetGraphSupplementaryData.oss';

import {getFunctionName, getTraversalDepth, getValue} from './util';
import {GraphTraverser} from '../app/GraphQueryImpl';
import {AssetGraphQueryItem} from '../asset-graph/useAssetGraphData';
import {buildRepoPathForHuman} from '../workspace/buildRepoAddress';
import {
  AllExpressionContext,
  AndExpressionContext,
  AttributeExpressionContext,
  CodeLocationAttributeExprContext,
  DownTraversalExpressionContext,
  FunctionCallExpressionContext,
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
  UpTraversalExpressionContext,
} from './generated/AssetSelectionParser';
import {AssetSelectionVisitor} from './generated/AssetSelectionVisitor';

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

  // Supplementary data is not used in oss
  constructor(all_assets: AssetGraphQueryItem[], _supplementaryData?: SupplementaryInformation) {
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
    let value: string | undefined = undefined;
    if (ctx.EQUAL()) {
      value = getValue(ctx.value(1));
    }
    return new Set(
      [...this.all_assets].filter((i) =>
        i.node.tags.some((t) => t.key === key && (!value || t.value === value)),
      ),
    );
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
