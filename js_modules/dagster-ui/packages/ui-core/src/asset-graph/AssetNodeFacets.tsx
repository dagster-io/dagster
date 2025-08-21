import {useMemo} from 'react';

import {AssetNodeFacet} from './AssetNodeFacetsUtil';
import {assertUnreachable} from '../app/Util';
import {useStateWithStorage} from '../hooks/useStateWithStorage';

export const AllAssetNodeFacets = [
  AssetNodeFacet.UnsyncedTag,
  AssetNodeFacet.Description,
  AssetNodeFacet.Owner,
  AssetNodeFacet.Checks,
  AssetNodeFacet.Freshness,
  AssetNodeFacet.LatestEvent,
  AssetNodeFacet.Status,
  AssetNodeFacet.KindTag,
  AssetNodeFacet.Automation,
];

export const AssetNodeFacetDefaults = [
  AssetNodeFacet.UnsyncedTag,
  AssetNodeFacet.Checks,
  AssetNodeFacet.LatestEvent,
  AssetNodeFacet.Status,
  AssetNodeFacet.KindTag,
  AssetNodeFacet.Automation,
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
    case AssetNodeFacet.Automation:
      return 'Automation';
    default:
      assertUnreachable(facet);
  }
}
