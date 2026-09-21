import {useMemo} from 'react';

import {tokenForAssetKey} from '../../asset-graph/Utils';
import {useAllAssets} from '../useAllAssets';

export type StorageAddressLike = {tableName: string; storageKind: string | null};

/**
 * Returns a normalized key for a storage address, or null if the address
 * has no table name. Two assets with the same key target the same
 * underlying table.
 */
export function storageAddressKey(addr: StorageAddressLike | null | undefined): string | null {
  return addr?.tableName?.toLowerCase() ?? null;
}

function storageKindMatches(a: string | null | undefined, b: string | null | undefined): boolean {
  return !!a && !!b && a.toLowerCase() === b.toLowerCase();
}

type AssetWithDefinition = {
  key: {path: string[]};
  definition: {
    storageAddress?: StorageAddressLike | null;
    repository: {location: {name: string}};
  } | null;
};

/**
 * Filters out connection-derived assets that share a storage address with
 * at least one non-connection (SDA) asset.
 */
export function filterConnectionDuplicates<T extends AssetWithDefinition>(
  assets: T[],
  connectionLocationNames: Set<string>,
): T[] {
  const sdaAddressCounts = new Map<string, number>();
  for (const a of assets) {
    if (!a.definition || connectionLocationNames.has(a.definition.repository.location.name)) {
      continue;
    }
    const key = storageAddressKey(a.definition.storageAddress);
    if (key) {
      sdaAddressCounts.set(key, (sdaAddressCounts.get(key) ?? 0) + 1);
    }
  }

  return assets.filter((a) => {
    if (!a.definition || !connectionLocationNames.has(a.definition.repository.location.name)) {
      return true;
    }
    const key = storageAddressKey(a.definition.storageAddress);
    return !key || (sdaAddressCounts.get(key) ?? 0) === 0;
  });
}

export type LinkedAssetResult =
  | {type: 'linked'; linkedAssetKey: {path: string[]}}
  | {type: 'ambiguous'}
  | {type: 'none'};

/**
 * Determines the linked asset for a given asset based on storage address matching.
 *
 * - Exactly one full match (tableName + storageKind) → linked
 * - No full matches, exactly one tableName match → linked
 * - Multiple full matches, or multiple tableName matches with no kind matches → ambiguous
 * - No tableName matches → none
 */
export function findLinkedAssetResult(
  currentAssetKey: {path: string[]},
  storageAddress: StorageAddressLike | null | undefined,
  assets: ReadonlyArray<{
    key: {path: string[]};
    definition?: {storageAddress?: StorageAddressLike | null} | null;
  }>,
): LinkedAssetResult {
  const currentTableName = storageAddress?.tableName?.toLowerCase();
  if (!currentTableName) {
    return {type: 'none'};
  }

  const currentToken = tokenForAssetKey(currentAssetKey);
  const tableMatches: Array<{path: string[]}> = [];
  const fullMatches: Array<{path: string[]}> = [];

  for (const asset of assets) {
    if (tokenForAssetKey(asset.key) === currentToken) {
      continue;
    }
    const candidateAddr = asset.definition?.storageAddress;
    if (!candidateAddr?.tableName) {
      continue;
    }
    if (candidateAddr.tableName.toLowerCase() !== currentTableName) {
      continue;
    }

    tableMatches.push({path: asset.key.path});
    if (storageKindMatches(storageAddress?.storageKind, candidateAddr.storageKind)) {
      fullMatches.push({path: asset.key.path});
    }
  }

  if (fullMatches.length === 1 && fullMatches[0]) {
    return {type: 'linked', linkedAssetKey: fullMatches[0]};
  }
  if (fullMatches.length > 1) {
    return {type: 'ambiguous'};
  }
  // No full matches — fall back to table-only matches
  if (tableMatches.length === 1 && tableMatches[0]) {
    return {type: 'linked', linkedAssetKey: tableMatches[0]};
  }
  if (tableMatches.length > 1) {
    return {type: 'ambiguous'};
  }
  return {type: 'none'};
}

export function useLinkedAsset({
  currentAssetKey,
  storageAddress,
}: {
  currentAssetKey: {path: string[]};
  storageAddress: StorageAddressLike | null | undefined;
}): LinkedAssetResult {
  const {assets} = useAllAssets();

  return useMemo(() => {
    if (!assets) {
      return {type: 'none' as const};
    }
    return findLinkedAssetResult(currentAssetKey, storageAddress, assets);
  }, [assets, currentAssetKey, storageAddress]);
}
