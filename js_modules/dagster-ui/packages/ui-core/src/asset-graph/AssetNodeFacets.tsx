import {useCallback, useMemo} from 'react';
import {assertUnreachable} from '../app/Util';
import {useStateWithStorage} from '../hooks/useStateWithStorage';

export enum AssetNodeFacet {
  UnsyncedTag = 'unsynced-tag',
  Description = 'description',
  Owner = 'owner',
  LatestEvent = 'latest-event',
  Checks = 'checks',
  Freshness = 'freshness',
  Status = 'status',
  KindTag = 'kind-tag',
}

export const AllAssetNodeFacets = [
  AssetNodeFacet.UnsyncedTag,
  AssetNodeFacet.Description,
  AssetNodeFacet.Owner,
  AssetNodeFacet.Checks,
  AssetNodeFacet.Freshness,
  AssetNodeFacet.LatestEvent,
  AssetNodeFacet.Status,
  AssetNodeFacet.KindTag,
];

export const AssetNodeFacetDefaults = [
  AssetNodeFacet.UnsyncedTag,
  AssetNodeFacet.Checks,
  AssetNodeFacet.Freshness,
  AssetNodeFacet.LatestEvent,
  AssetNodeFacet.Status,
  AssetNodeFacet.KindTag,
];

function validateSavedFacets(input: any) {
  return input && Array.isArray(input)
    ? input.filter((key) => AllAssetNodeFacets.includes(key))
    : AssetNodeFacetDefaults;
}

export function useSavedAssetNodeFacets() {
  const [val, setVal] = useStateWithStorage('asset-node-facets', validateSavedFacets);
  return useMemo(() => {
    return [new Set(val), (next: Set<AssetNodeFacet>) => setVal(Array.from(next))] as const;
  }, [val, setVal]);
}

export function labelForFacet(facet: AssetNodeFacet) {
  switch (facet) {
    case AssetNodeFacet.Status:
      return 'Status';
    case AssetNodeFacet.Owner:
      return 'Owner';
    case AssetNodeFacet.Description:
      return 'Description';
    case AssetNodeFacet.Checks:
      return 'Asset checks';
    case AssetNodeFacet.Freshness:
      return 'Freshness';
    case AssetNodeFacet.LatestEvent:
      return 'Latest event';
    case AssetNodeFacet.KindTag:
      return 'Kind tag';
    case AssetNodeFacet.UnsyncedTag:
      return 'Sync status tags';
    default:
      assertUnreachable(facet);
  }
}
