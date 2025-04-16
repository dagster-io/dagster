import {useMemo} from 'react';

import {useAssetsHealthData} from '../asset-data/AssetHealthDataProvider';
import {parseExpression} from '../asset-selection/AssetSelectionSupplementaryDataVisitor';
import {getSupplementaryDataKey} from '../asset-selection/util';
import {AssetKey} from '../assets/types';
import {AssetNodeForGraphQueryFragment} from './types/useAssetGraphData.types';
import {SupplementaryInformation} from '../asset-selection/types';

const emptyObject = {} as SupplementaryInformation;
export const useAssetGraphSupplementaryData = (
  selection: string,
  nodes: AssetNodeForGraphQueryFragment[],
): {loading: boolean; data: SupplementaryInformation} => {
  const {liveDataByNode} = useAssetsHealthData(
    useMemo(() => nodes.map((node) => node.assetKey), [nodes]),
  );

  const loading = Object.keys(liveDataByNode).length !== nodes.length;

  const assetsByStatus = useMemo(() => {
    return Object.values(liveDataByNode).reduce(
      (acc, liveData) => {
        const status = liveData.assetHealth?.assetHealth ?? 'UNKNOWN';
        const supplementaryDataKey = getSupplementaryDataKey({
          field: 'status',
          value: status,
        });
        acc[supplementaryDataKey] = acc[supplementaryDataKey] || [];
        acc[supplementaryDataKey].push(liveData.assetKey);
        return acc;
      },
      {} as Record<string, AssetKey[]>,
    );
  }, [liveDataByNode]);

  const needsAssetHealthData = useMemo(() => {
    const filters = parseExpression(selection);
    return filters.some((filter) => filter.field === 'status');
  }, [selection]);

  return {
    loading: needsAssetHealthData && loading,
    data: loading ? emptyObject : assetsByStatus,
  };
};
