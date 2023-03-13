import {ReleasesWorkspace_RAW} from './LaunchAssetLoaderQuery.fixtures';

export const ReleasesJobProps = {
  assets: ReleasesWorkspace_RAW.result.data.assetNodes,
  upstreamAssetKeys: [],
  repoAddress: {
    name: '__repository__',
    location: 'assets_dynamic_partitions',
  },
  target: {
    type: 'job' as const,
    jobName: '__ASSET_JOB_0',
    partitionSetName: '__ASSET_JOB_0_partition_set',
  },
  open: true,
};
