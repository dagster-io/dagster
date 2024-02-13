// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type DaemonNotRunningAlertInstanceFragment = {
  __typename: 'Instance';
  id: string;
  daemonHealth: {
    __typename: 'DaemonHealth';
    id: string;
    daemonStatus: {__typename: 'DaemonStatus'; id: string; healthy: boolean | null};
  };
};

export type UsingDefaultLauncherAlertInstanceFragment = {
  __typename: 'Instance';
  id: string;
  runQueuingSupported: boolean;
  runLauncher: {__typename: 'RunLauncher'; name: string} | null;
};
