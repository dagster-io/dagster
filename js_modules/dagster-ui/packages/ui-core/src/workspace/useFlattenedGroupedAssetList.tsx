import {useMemo} from 'react';

import {repoAddressAsHumanString} from './repoAddressAsString';
import {RepoAddress} from './types';
import {RepoAssetTableFragment} from './types/WorkspaceAssetsQuery.types';
import {COMMON_COLLATOR} from '../app/Util';
import {displayNameForAssetKey} from '../asset-graph/Utils';
import {usePersistedExpansionState} from '../ui/usePersistedExpansionState';

type Asset = RepoAssetTableFragment;

type RowType =
  | {type: 'group'; name: string; assetCount: number}
  | {type: 'asset'; id: string; definition: Asset};

const UNGROUPED_NAME = 'UNGROUPED';
const ASSET_GROUPS_EXPANSION_STATE_STORAGE_KEY = 'assets-virtualized-expansion-state';

type Config = {
  repoAddress: RepoAddress;
  assets: Asset[];
};

export const useFlattenedGroupedAssetList = ({repoAddress, assets}: Config) => {
  const repoKey = repoAddressAsHumanString(repoAddress);
  const {expandedKeys, onToggle} = usePersistedExpansionState(
    `${repoKey}-${ASSET_GROUPS_EXPANSION_STATE_STORAGE_KEY}`,
  );

  const grouped: Record<string, Asset[]> = useMemo(() => {
    const groups: Record<string, Asset[]> = {};
    for (const asset of assets) {
      const groupName = asset.groupName || UNGROUPED_NAME;
      if (!groups[groupName]) {
        groups[groupName] = [];
      }
      groups[groupName]!.push(asset);
    }

    Object.values(groups).forEach((group) => {
      group.sort((a, b) =>
        COMMON_COLLATOR.compare(
          displayNameForAssetKey(a.assetKey),
          displayNameForAssetKey(b.assetKey),
        ),
      );
    });

    return groups;
  }, [assets]);

  const flattened: RowType[] = useMemo(() => {
    const flat: RowType[] = [];
    Object.entries(grouped)
      .sort(([aName], [bName]) => COMMON_COLLATOR.compare(aName, bName))
      .forEach(([groupName, assetsForGroup]) => {
        flat.push({type: 'group', name: groupName, assetCount: assetsForGroup.length});
        if (expandedKeys.includes(groupName)) {
          assetsForGroup.forEach((asset) => {
            flat.push({type: 'asset', id: asset.id, definition: asset});
          });
        }
      });
    return flat;
  }, [grouped, expandedKeys]);

  return {flattened, expandedKeys: new Set(expandedKeys), onToggle};
};
