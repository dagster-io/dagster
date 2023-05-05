import {MockedResponse} from '@apollo/client/testing';

import {
  buildDaemonHealth,
  buildDaemonStatus,
  buildInstance,
  buildRunLauncher,
} from '../../graphql/types';
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
      instance: buildInstance({
        daemonHealth: buildDaemonHealth({
          id: 'daemonHealth',
          daemonStatus: buildDaemonStatus({
            id: 'BACKFILL',
            healthy: false,
          }),
        }),
        runQueuingSupported: false,
        runLauncher: buildRunLauncher({
          name: 'DefaultRunLauncher',
        }),
      }),
    },
  },
};
