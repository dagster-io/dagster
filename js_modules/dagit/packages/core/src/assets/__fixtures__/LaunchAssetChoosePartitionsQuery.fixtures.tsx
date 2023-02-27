import {MockedResponse} from '@apollo/client/testing';

import {LAUNCH_ASSET_CHOOSE_PARTITIONS_QUERY} from '../LaunchAssetChoosePartitionsDialog';
import {LaunchAssetChoosePartitionsQuery} from '../types/LaunchAssetChoosePartitionsDialog.types';

export const ReleasesWorkspace: MockedResponse<LaunchAssetChoosePartitionsQuery> = {
  request: {
    query: LAUNCH_ASSET_CHOOSE_PARTITIONS_QUERY,
    variables: {},
  },
  result: {
    data: {
      __typename: 'DagitQuery',
      instance: {
        daemonHealth: {
          id: 'daemonHealth',
          daemonStatus: {
            id: 'BACKFILL',
            healthy: false,
            __typename: 'DaemonStatus',
          },
          __typename: 'DaemonHealth',
        },
        __typename: 'Instance',
        runQueuingSupported: false,
        runLauncher: {
          name: 'DefaultRunLauncher',
          __typename: 'RunLauncher',
        },
      },
    },
  },
};
