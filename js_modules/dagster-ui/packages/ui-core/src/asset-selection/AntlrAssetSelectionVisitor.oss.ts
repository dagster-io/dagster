import {AbstractParseTreeVisitor, ParseTree} from 'antlr4ng';
import escapeRegExp from 'lodash/escapeRegExp';

import {SupplementaryInformation} from './types';
import {
  getAssetsByKey,
  getFunctionName,
  getSupplementaryDataKey,
  getTraversalDepth,
  getValue,
  isNullValue,
} from './util';
import {GraphTraverser} from '../app/GraphQueryImpl';
import {tokenForAssetKey} from '../asset-graph/Utils';
import {AssetGraphQueryItem} from '../asset-graph/types';
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
  KindAttributeExprContext,
  NotExpressionContext,
  OrExpressionContext,
  OwnerAttributeExprContext,
  ParenthesizedExpressionContext,
  StartContext,
  StatusAttributeExprContext,
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
  protected all_assets: Set<AssetGraphQueryItem>;
  public focus_assets: Set<AssetGraphQueryItem>;
  protected traverser: GraphTraverser<AssetGraphQueryItem>;
  protected supplementaryData: SupplementaryInformation;
  protected allAssetsByKey: Map<string, AssetGraphQueryItem>;

  protected defaultResult() {
    return new Set<AssetGraphQueryItem>();
  }

  /** Helper to visit a nullable context and return defaultResult() if null */
  private visitOrDefault(ctx: ParseTree | null): Set<AssetGraphQueryItem> {
    return ctx ? (this.visit(ctx) ?? this.defaultResult()) : this.defaultResult();
  }

  // Supplementary data is not used in oss
  constructor(all_assets: AssetGraphQueryItem[], supplementaryData: SupplementaryInformation) {
    super();
    this.all_assets = new Set(all_assets);
    this.focus_assets = new Set();
    this.traverser = new GraphTraverser(all_assets);
    this.supplementaryData = supplementaryData;
    this.allAssetsByKey = getAssetsByKey(all_assets);
  }

  visitStart(ctx: StartContext) {
    return this.visitOrDefault(ctx.expr());
  }

  visitTraversalAllowedExpression(ctx: TraversalAllowedExpressionContext) {
    return this.visitOrDefault(ctx.traversalAllowedExpr());
  }

  visitUpAndDownTraversalExpression(ctx: UpAndDownTraversalExpressionContext) {
    const selection = this.visitOrDefault(ctx.traversalAllowedExpr());
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
    const selection = this.visitOrDefault(ctx.traversalAllowedExpr());
    const upTraversal = ctx.upTraversal();
    const traversal_depth = upTraversal ? getTraversalDepth(upTraversal) : 0;
    const selection_copy = new Set(selection);
    for (const item of selection_copy) {
      this.traverser.fetchUpstream(item, traversal_depth).forEach((i) => selection.add(i));
    }
    return selection;
  }

  visitDownTraversalExpression(ctx: DownTraversalExpressionContext) {
    const selection = this.visitOrDefault(ctx.traversalAllowedExpr());
    const downTraversal = ctx.downTraversal();
    const traversal_depth = downTraversal ? getTraversalDepth(downTraversal) : 0;
    const selection_copy = new Set(selection);
    for (const item of selection_copy) {
      this.traverser.fetchDownstream(item, traversal_depth).forEach((i) => selection.add(i));
    }
    return selection;
  }

  visitNotExpression(ctx: NotExpressionContext) {
    const selection = this.visitOrDefault(ctx.expr());
    return new Set([...this.all_assets].filter((i) => !selection.has(i)));
  }

  visitAndExpression(ctx: AndExpressionContext) {
    const left = this.visitOrDefault(ctx.expr(0));
    const right = this.visitOrDefault(ctx.expr(1));
    return new Set([...left].filter((i) => right.has(i)));
  }

  visitOrExpression(ctx: OrExpressionContext) {
    const left = this.visitOrDefault(ctx.expr(0));
    const right = this.visitOrDefault(ctx.expr(1));
    return new Set([...left, ...right]);
  }

  visitAllExpression(_ctx: AllExpressionContext) {
    return this.all_assets;
  }

  visitAttributeExpression(ctx: AttributeExpressionContext) {
    return this.visitOrDefault(ctx.attributeExpr());
  }

  visitFunctionCallExpression(ctx: FunctionCallExpressionContext) {
    const funcName = ctx.functionName();
    const function_name = funcName ? getFunctionName(funcName) : '';
    const selection = this.visitOrDefault(ctx.expr());
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
    return this.visitOrDefault(ctx.expr());
  }

  visitKeyExpr(ctx: KeyExprContext) {
    const keyValue = ctx.keyValue();
    const value = keyValue ? getValue(keyValue) : '';
    const regex: RegExp = new RegExp(`^${escapeRegExp(value).replaceAll('\\*', '.*')}$`);
    const selection = [...this.all_assets].filter((i) => regex.test(i.name));

    selection.forEach((i) => this.focus_assets.add(i));
    return new Set(selection);
  }

  visitTagAttributeExpr(ctx: TagAttributeExprContext) {
    const keyCtx = ctx.value(0);
    const key = keyCtx ? getValue(keyCtx) : '';
    let value: string | undefined = undefined;
    if (ctx.EQUAL()) {
      const valueCtx = ctx.value(1);
      value = valueCtx ? getValue(valueCtx) : undefined;
    }
    const isNullKey = keyCtx ? isNullValue(keyCtx) : false;
    return new Set(
      [...this.all_assets].filter((i) => {
        if (i.node.tags.length > 0) {
          return i.node.tags.some(
            (t) => t.key === key && ((!value && t.value === '') || t.value === value),
          );
        }
        return isNullKey && !value;
      }),
    );
  }

  visitOwnerAttributeExpr(ctx: OwnerAttributeExprContext) {
    const valueCtx = ctx.value();
    const value = valueCtx ? getValue(valueCtx) : '';
    const isNull = valueCtx ? isNullValue(valueCtx) : false;
    return new Set(
      [...this.all_assets].filter((i) => {
        if (i.node.owners.length > 0) {
          return i.node.owners.some((o) => {
            if (o.__typename === 'TeamAssetOwner') {
              return o.team === value;
            } else {
              return o.email === value;
            }
          });
        }
        return isNull;
      }),
    );
  }

  visitGroupAttributeExpr(ctx: GroupAttributeExprContext) {
    const valueCtx = ctx.value();
    const value = valueCtx ? getValue(valueCtx) : '';
    const isNull = valueCtx ? isNullValue(valueCtx) : false;
    return new Set(
      [...this.all_assets].filter((i) => {
        if (i.node.groupName) {
          return i.node.groupName === value;
        }
        return isNull;
      }),
    );
  }

  visitKindAttributeExpr(ctx: KindAttributeExprContext) {
    const valueCtx = ctx.value();
    const value = valueCtx ? getValue(valueCtx) : '';
    const isNull = valueCtx ? isNullValue(valueCtx) : false;
    return new Set(
      [...this.all_assets].filter((i) => {
        if (i.node.kinds.length > 0) {
          return i.node.kinds.some((k) => k === value);
        }
        return isNull;
      }),
    );
  }

  visitCodeLocationAttributeExpr(ctx: CodeLocationAttributeExprContext) {
    const valueCtx = ctx.value();
    const value = valueCtx ? getValue(valueCtx) : '';
    const selection = new Set<AssetGraphQueryItem>();
    for (const asset of this.all_assets) {
      const repository = asset.node.repository;
      const location = repository.name
        ? buildRepoPathForHuman(repository.name, repository.location.name)
        : '';
      if (location === value) {
        selection.add(asset);
      }
    }
    return selection;
  }

  visitStatusAttributeExpr(ctx: StatusAttributeExprContext) {
    const valueCtx = ctx.value();
    const statusName = valueCtx ? getValue(valueCtx) : '';
    const supplementaryDataKey = getSupplementaryDataKey({
      field: 'status',
      value: statusName.toUpperCase(),
    });
    const matchingAssetKeys = this.supplementaryData?.[supplementaryDataKey];
    if (!matchingAssetKeys) {
      return new Set<AssetGraphQueryItem>();
    }
    return new Set(
      matchingAssetKeys
        .map((key) => this.allAssetsByKey.get(tokenForAssetKey(key)))
        .filter((item): item is AssetGraphQueryItem => item !== undefined),
    );
  }
}
