// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type DaemonHealthFragment = {
  __typename: 'DaemonHealth';
  id: string;
  allDaemonStatuses: Array<{
    __typename: 'DaemonStatus';
    id: string;
    daemonType: string;
    required: boolean;
    healthy: boolean | null;
    lastHeartbeatTime: number | null;
    lastHeartbeatErrors: Array<{
      __typename: 'PythonError';
      message: string;
      stack: Array<string>;
      errorChain: Array<{
        __typename: 'ErrorChainLink';
        isExplicitLink: boolean;
        error: {__typename: 'PythonError'; message: string; stack: Array<string>};
      }>;
    }>;
  }>;
};

export type DaemonStatusForListFragment = {
  __typename: 'DaemonStatus';
  id: string;
  daemonType: string;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatTime: number | null;
  lastHeartbeatErrors: Array<{
    __typename: 'PythonError';
    message: string;
    stack: Array<string>;
    errorChain: Array<{
      __typename: 'ErrorChainLink';
      isExplicitLink: boolean;
      error: {__typename: 'PythonError'; message: string; stack: Array<string>};
    }>;
  }>;
};
