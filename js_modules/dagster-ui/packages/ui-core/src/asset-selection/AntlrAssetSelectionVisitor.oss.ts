import {AbstractParseTreeVisitor} from 'antlr4ng';
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
    return new Set([...this.all_assets].filter((i) => !selection.has(i)));
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
    return this.all_assets;
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
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    return this.visit(ctx.expr()!) ?? this.defaultResult();
  }

  visitKeyExpr(ctx: KeyExprContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const value: string = getValue(ctx.keyValue()!);
    const regex: RegExp = new RegExp(`^${escapeRegExp(value).replaceAll('\\*', '.*')}$`);
    const selection = [...this.all_assets].filter((i) => regex.test(i.name));

    selection.forEach((i) => this.focus_assets.add(i));
    return new Set(selection);
  }

  visitTagAttributeExpr(ctx: TagAttributeExprContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const key: string = getValue(ctx.value(0)!);
    let value: string | undefined = undefined;
    if (ctx.EQUAL()) {
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      value = getValue(ctx.value(1)!);
    }
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const isNullKey = isNullValue(ctx.value(0)!);
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
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const value: string = getValue(ctx.value()!);
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const isNull = isNullValue(ctx.value()!);
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
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const value: string = getValue(ctx.value()!);
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const isNull = isNullValue(ctx.value()!);
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
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const value: string = getValue(ctx.value()!);
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const isNull = isNullValue(ctx.value()!);
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
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const value: string = getValue(ctx.value()!);
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
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const statusName: string = getValue(ctx.value()!);
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
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        .map((key) => this.allAssetsByKey.get(tokenForAssetKey(key))!)
        .filter(Boolean),
    );
  }
}
