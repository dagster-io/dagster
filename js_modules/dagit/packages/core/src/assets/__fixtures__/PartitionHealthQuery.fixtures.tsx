import {MockedResponse} from '@apollo/client/testing';

import {PartitionHealthQuery} from '../types/usePartitionHealthData.types';
import {PARTITION_HEALTH_QUERY} from '../usePartitionHealthData';

export const buildPartitionHealthMock = (
  assetKey: string,
  empty = false,
): MockedResponse<PartitionHealthQuery> => ({
  request: {
    query: PARTITION_HEALTH_QUERY,
    variables: {
      assetKey: {
        path: [assetKey],
      },
    },
  },
  result: {
    data: {
      __typename: 'DagitQuery',
      assetNodeOrError: {
        id: `assets_dynamic_partitions.__repository__.["${assetKey}"]`,
        partitionKeysByDimension: [
          {
            name: 'default',
            partitionKeys: empty ? [] : ['test1', 'test2'],
            __typename: 'DimensionPartitionKeys',
          },
        ],
        assetPartitionStatuses: {
          materializedPartitions: ['test1'],
          __typename: 'DefaultPartitions',
        },
        __typename: 'AssetNode',
      },
    },
  },
});

export const ReleaseZips = (empty?: boolean): MockedResponse<PartitionHealthQuery> =>
  buildPartitionHealthMock('release_zips', empty);

export const ReleaseFiles = (empty?: boolean): MockedResponse<PartitionHealthQuery> =>
  buildPartitionHealthMock('release_files', empty);

export const ReleaseFilesMetadata = (empty?: boolean): MockedResponse<PartitionHealthQuery> =>
  buildPartitionHealthMock('release_files_metadata', empty);

export const ReleasesSummary = (empty?: boolean): MockedResponse<PartitionHealthQuery> =>
  buildPartitionHealthMock('releases_summary', empty);

export const ReleasesMetadata = (empty?: boolean): MockedResponse<PartitionHealthQuery> =>
  buildPartitionHealthMock('releases_metadata', empty);
