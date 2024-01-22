import {StatusCase, buildAssetNodeStatusContent} from './AssetNodeStatusContent';
import {LiveDataForNode, tokenForAssetKey} from './Utils';
import {AssetKeyInput} from '../graphql/types';

export function groupAssetsByStatus<
  T extends {
    key: AssetKeyInput;
    definition?: {opNames: string[]; isSource: boolean; isObservable: boolean} | null;
  },
>(assets: T[], liveDataByNode: Record<string, LiveDataForNode>) {
  type StatusesType = {
    asset: T;
    status: ReturnType<typeof buildAssetNodeStatusContent>;
  };
  const statuses = {
    successful: [] as StatusesType[],
    failed: [] as StatusesType[],
    inprogress: [] as StatusesType[],
    missing: [] as StatusesType[],
    loading: false,
  };
  if (!Object.keys(liveDataByNode).length) {
    statuses.loading = true;
    return statuses;
  }
  Object.keys(liveDataByNode).forEach((key) => {
    const assetLiveData = liveDataByNode[key];
    const asset = assets.find((asset) => tokenForAssetKey(asset.key) === key);
    if (!asset?.definition) {
      console.warn('Expected a definition for asset with key', key);
      return;
    }
    const status = buildAssetNodeStatusContent({
      assetKey: asset.key,
      definition: asset.definition,
      liveData: assetLiveData,
      expanded: true,
    });
    switch (status.case) {
      case StatusCase.LOADING:
        statuses.loading = true;
        break;
      case StatusCase.SOURCE_OBSERVING:
        statuses.inprogress.push({asset, status});
        break;
      case StatusCase.SOURCE_OBSERVED:
        statuses.successful.push({asset, status});
        break;
      case StatusCase.SOURCE_NEVER_OBSERVED:
        statuses.missing.push({asset, status});
        break;
      case StatusCase.SOURCE_NO_STATE:
        statuses.missing.push({asset, status});
        break;
      case StatusCase.MATERIALIZING:
        statuses.inprogress.push({asset, status});
        break;
      case StatusCase.LATE_OR_FAILED:
        statuses.failed.push({asset, status});
        break;
      case StatusCase.NEVER_MATERIALIZED:
        statuses.missing.push({asset, status});
        break;
      case StatusCase.MATERIALIZED:
        statuses.successful.push({asset, status});
        break;
      case StatusCase.PARTITIONS_FAILED:
        statuses.failed.push({asset, status});
        break;
      case StatusCase.PARTITIONS_MISSING:
        statuses.missing.push({asset, status});
        break;
      case StatusCase.PARTITIONS_MATERIALIZED:
        statuses.successful.push({asset, status});
        break;
    }
  });
  return statuses;
}
