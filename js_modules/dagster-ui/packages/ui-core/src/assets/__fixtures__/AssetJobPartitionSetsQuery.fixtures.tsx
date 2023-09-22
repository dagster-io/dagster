import {MockedResponse} from '@apollo/client/testing';

import {AssetJobPartitionSetsQuery} from '../types/usePartitionNameForPipeline.types';
import {ASSET_JOB_PARTITION_SETS_QUERY} from '../usePartitionNameForPipeline';

export const ReleasesWorkspace: MockedResponse<AssetJobPartitionSetsQuery> = {
  request: {
    query: ASSET_JOB_PARTITION_SETS_QUERY,
    variables: {},
  },
  result: {
    data: {
      __typename: 'Query',
      partitionSetsOrError: {
        __typename: 'PartitionSets',
        results: [
          {
            id: '4d66ae94818f6f90315ea7653c4b2e259fe114cb',
            name: '__ASSET_JOB_0_partition_set',
            mode: 'default',
            solidSelection: null,
            __typename: 'PartitionSet',
          },
        ],
      },
    },
  },
};
