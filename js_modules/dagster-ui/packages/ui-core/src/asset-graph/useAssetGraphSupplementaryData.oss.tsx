import {useMemo} from 'react';

import {useAssetsHealthData} from '../asset-data/AssetHealthDataProvider';
import {parseExpression} from '../asset-selection/AssetSelectionSupplementaryDataVisitor';
import {SupplementaryInformation} from '../asset-selection/types';
import {getSupplementaryDataKey} from '../asset-selection/util';
import {AssetKey} from '../assets/types';
import {useStableReferenceByHash} from '../hooks/useStableReferenceByHash';
import {WorkspaceAssetFragment} from '../workspace/WorkspaceContext/types/WorkspaceQueries.types';

const emptyObject = {} as SupplementaryInformation;
export const useAssetGraphSupplementaryData = (
  selection: string,
  nodes: WorkspaceAssetFragment[],
): {loading: boolean; data: SupplementaryInformation} => {
  const {liveDataByNode} = useAssetsHealthData({
    assetKeys: useMemo(() => nodes.map((node) => node.assetKey), [nodes]),
    thread: 'AssetGraphSupplementaryData', // Separate thread to avoid starving UI
    blockTrace: false,
  });

  const loading = Object.keys(liveDataByNode).length !== nodes.length;

  const assetsByStatus = useMemo(() => {
    if (loading) {
      return emptyObject;
    }
    return Object.values(liveDataByNode).reduce(
      (acc, liveData) => {
        const status = liveData.assetHealth?.assetHealth ?? 'UNKNOWN';
        const supplementaryDataKey = getSupplementaryDataKey({
          field: 'status',
          value: status,
        });
        acc[supplementaryDataKey] = acc[supplementaryDataKey] || [];
        acc[supplementaryDataKey].push(liveData.key);
        return acc;
      },
      {} as Record<string, AssetKey[]>,
    );
  }, [liveDataByNode, loading]);

  const needsAssetHealthData = useMemo(() => {
    try {
      const filters = parseExpression(selection);
      return filters.some((filter) => filter.field === 'status');
    } catch {
      return false;
    }
  }, [selection]);

  const data = useStableReferenceByHash(assetsByStatus, true);

  return {
    loading: needsAssetHealthData && loading,
    data: loading ? emptyObject : data,
  };
};
