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

export type DaemonNotRunningAlertQueryVariables = Types.Exact<{[key: string]: never}>;

export type DaemonNotRunningAlertQuery = {
  __typename: 'Query';
  instance: {
    __typename: 'Instance';
    id: string;
    daemonHealth: {
      __typename: 'DaemonHealth';
      id: string;
      daemonStatus: {__typename: 'DaemonStatus'; id: string; healthy: boolean | null};
    };
  };
};

export type UsingDefaultLauncherAlertInstanceFragment = {
  __typename: 'Instance';
  id: string;
  runQueuingSupported: boolean;
  runLauncher: {__typename: 'RunLauncher'; name: string} | null;
};

export const DaemonNotRunningAlertQueryVersion = 'f016870739b8816036750fb916c536889c862b5d591bf7c552f5cdefde693539';
