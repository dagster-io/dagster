import {MockedResponse} from '@apollo/client/testing';

import {
  buildDaemonHealth,
  buildDaemonStatus,
  buildInstance,
  buildRunLauncher,
} from '../../graphql/types';
import {LAUNCH_ASSET_WARNINGS_QUERY} from '../LaunchAssetChoosePartitionsDialog';
import {LaunchAssetWarningsQuery} from '../types/LaunchAssetChoosePartitionsDialog.types';

export const ReleasesWorkspace: MockedResponse<LaunchAssetWarningsQuery> = {
  request: {
    query: LAUNCH_ASSET_WARNINGS_QUERY,
    variables: {},
  },
  result: {
    data: {
      __typename: 'Query',
      assetNodes: [],
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
