import {useMemo} from 'react';

import {tokenForAssetKey} from './Utils';
import {useAssetsHealthData} from '../asset-data/AssetHealthDataProvider';
import {AssetHealthFragment} from '../asset-data/types/AssetHealthDataProvider.types';
import {parseExpression} from '../asset-selection/AssetSelectionSupplementaryDataVisitor';
import {SupplementaryInformation} from '../asset-selection/types';
import {getSupplementaryDataKey} from '../asset-selection/util';
import {AssetKey} from '../assets/types';
import {Asset, useAllAssets} from '../assets/useAllAssets';
import {AssetHealthStatus} from '../graphql/types';
import {useStableReferenceByHash} from '../hooks/useStableReferenceByHash';
import {WorkspaceAssetFragment} from '../workspace/WorkspaceContext/types/WorkspaceQueries.types';

const emptyObject = {} as SupplementaryInformation;
export const useAssetGraphSupplementaryData = (
  selection: string,
  nodes: WorkspaceAssetFragment[],
): {loading: boolean; data: SupplementaryInformation} => {
  const needsAssetHealthData = useMemo(() => {
    try {
      const filters = parseExpression(selection);
      return filters.some((filter) => filter.field === 'status');
    } catch {
      return false;
    }
  }, [selection]);

  const {liveDataByNode} = useAssetsHealthData({
    assetKeys: useMemo(() => nodes.map((node) => node.assetKey), [nodes]),
    thread: 'AssetGraphSupplementaryData', // Separate thread to avoid starving UI
    blockTrace: false,
    skip: !needsAssetHealthData,
  });

  const {assetsByAssetKey} = useAllAssets();

  const loading = Object.keys(liveDataByNode).length !== nodes.length;

  const assetsByStatus = useMemo(() => {
    if (loading) {
      return emptyObject;
    }
    return Object.values(liveDataByNode).reduce(
      (acc, liveData) => {
        const status = liveData.assetHealth?.assetHealth ?? 'UNKNOWN';
        const asset = assetsByAssetKey.get(tokenForAssetKey(liveData.key)) ?? null;
        const materializationStatus = getMaterializationStatus(liveData, asset);
        const freshnessStatus = getFreshnessStatus(liveData, asset);
        const checkStatus = getCheckStatus(liveData, asset);

        function addStatusValue(value: string) {
          const supplementaryDataKey = getSupplementaryDataKey({
            field: 'status',
            value,
          });
          acc[supplementaryDataKey] = acc[supplementaryDataKey] || [];
          acc[supplementaryDataKey].push(liveData.key);
        }

        addStatusValue(status);
        addStatusValue(materializationStatus);
        addStatusValue(freshnessStatus);
        addStatusValue(checkStatus);
        return acc;
      },
      {} as Record<string, AssetKey[]>,
    );
  }, [assetsByAssetKey, liveDataByNode, loading]);

  const data = useStableReferenceByHash(assetsByStatus);

  return {
    loading: needsAssetHealthData && loading,
    data: loading ? emptyObject : data,
  };
};

export function getMaterializationStatus(healthData: AssetHealthFragment, _asset: Asset | null) {
  if (healthData.assetHealth?.materializationStatus === AssetHealthStatus.HEALTHY) {
    return 'MATERIALIZATION_SUCCESS';
  }
  if (healthData.assetHealth?.materializationStatus === AssetHealthStatus.UNKNOWN) {
    return 'MATERIALIZATION_UNKNOWN';
  }
  return 'MATERIALIZATION_FAILURE';
}

export function getFreshnessStatus(healthData: AssetHealthFragment, asset: Asset | null) {
  if (healthData.assetHealth?.freshnessStatus === AssetHealthStatus.HEALTHY) {
    return 'FRESHNESS_PASSING';
  }
  if (healthData.assetHealth?.freshnessStatus === AssetHealthStatus.WARNING) {
    return 'FRESHNESS_WARNING';
  }
  if (healthData.assetHealth?.freshnessStatus === AssetHealthStatus.DEGRADED) {
    return 'FRESHNESS_FAILURE';
  }
  if (asset?.definition?.internalFreshnessPolicy) {
    return 'FRESHNESS_UNKNOWN';
  }
  return 'FRESHNESS_MISSING';
}

export function getCheckStatus(healthData: AssetHealthFragment, asset: Asset | null) {
  if (healthData.assetHealth?.assetChecksStatus === AssetHealthStatus.HEALTHY) {
    return 'CHECK_PASSING';
  }
  if (healthData.assetHealth?.assetChecksStatus === AssetHealthStatus.WARNING) {
    return 'CHECK_WARNING';
  }
  if (healthData.assetHealth?.assetChecksStatus === AssetHealthStatus.DEGRADED) {
    return 'CHECK_FAILURE';
  }
  if (asset?.definition?.hasAssetChecks) {
    return 'CHECK_UNKNOWN';
  }
  return 'CHECK_MISSING';
}
