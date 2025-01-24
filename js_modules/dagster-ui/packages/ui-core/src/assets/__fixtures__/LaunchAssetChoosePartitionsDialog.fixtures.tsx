import {assetNodes} from './LaunchAssetLoaderQuery.fixtures';
import {LaunchAssetChoosePartitionsDialogProps} from '../LaunchAssetChoosePartitionsDialog';

export const ReleasesJobProps: Omit<LaunchAssetChoosePartitionsDialogProps, 'open' | 'setOpen'> = {
  assets: assetNodes,
  upstreamAssetKeys: [],
  repositorySelector: {
    repositoryName: '__repository__',
    repositoryLocationName: 'assets_dynamic_partitions',
  },
  target: {
    type: 'job' as const,
    jobName: '__ASSET_JOB_0',
    assetKeys: [{path: ['asset_key_1']}],
  },
};
