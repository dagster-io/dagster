import {tokenForAssetKey} from '../asset-graph/Utils';
import {AssetKey} from '../assets/types';
import {weakMapMemoize} from '../util/weakMapMemoize';
import {
  DownTraversalContext,
  FunctionNameContext,
  KeyValueContext,
  UpTraversalContext,
  ValueContext,
} from './generated/AssetSelectionParser';
import {ValueContext as OpSelectionValueContext} from '../op-selection/generated/OpSelectionParser';
import {ValueContext as RunSelectionValueContext} from '../run-selection/generated/RunSelectionParser';

export function getTraversalDepth(ctx: UpTraversalContext | DownTraversalContext): number {
  const digits = ctx.DIGITS();
  if (digits) {
    return parseInt(ctx.getText());
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

export function getValue(
  ctx: ValueContext | KeyValueContext | OpSelectionValueContext | RunSelectionValueContext,
): string {
  if (ctx.QUOTED_STRING()) {
    return ctx.getText().slice(1, -1);
  }
  if (ctx.UNQUOTED_STRING()) {
    return ctx.getText();
  }
  if ('UNQUOTED_WILDCARD_STRING' in ctx && ctx.UNQUOTED_WILDCARD_STRING()) {
    return ctx.getText();
  }
  if ('NULL_STRING' in ctx && ctx.NULL_STRING()) {
    return '';
  }
  throw new Error('Invalid value');
}

export function isNullValue(ctx: Pick<ValueContext, 'NULL_STRING'>): boolean {
  if ('NULL_STRING' in ctx && ctx.NULL_STRING()) {
    return true;
  }
  return false;
}

export function getSupplementaryDataKey({
  field,
  value,
}: {
  field: string;
  value: string | {key: string; value?: string | undefined};
}): string {
  return JSON.stringify({field, value});
}

export const getAssetsByKey = weakMapMemoize(
  <T extends {node: {assetKey: AssetKey}} | {key: AssetKey} | {assetKey: AssetKey}>(
    all_assets: T[],
  ) => {
    const assetsByKey = new Map<string, T>();
    for (const asset of all_assets) {
      let key;
      if ('node' in asset) {
        key = asset.node.assetKey;
      } else if ('key' in asset) {
        key = asset.key;
      } else {
        key = asset.assetKey;
      }
      assetsByKey.set(tokenForAssetKey(key), asset);
    }
    return assetsByKey;
  },
);
