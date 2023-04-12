// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type LaunchAssetChoosePartitionsQueryVariables = Types.Exact<{[key: string]: never}>;

export type LaunchAssetChoosePartitionsQuery = {
  __typename: 'DagitQuery';
  instance: {
    __typename: 'Instance';
    id: string;
    runQueuingSupported: boolean;
    daemonHealth: {
      __typename: 'DaemonHealth';
      id: string;
      daemonStatus: {__typename: 'DaemonStatus'; id: string; healthy: boolean | null};
    };
    runLauncher: {__typename: 'RunLauncher'; name: string} | null;
  };
};
