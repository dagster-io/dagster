// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type InstanceHealthQueryVariables = Types.Exact<{[key: string]: never}>;

export type InstanceHealthQuery = {
  __typename: 'Query';
  instance: {
    __typename: 'Instance';
    id: string;
    hasInfo: boolean;
    daemonHealth: {
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
  };
};

export const InstanceHealthQueryVersion = '287f4e065bba5aba76b6c1e1a58f0f929c0b37e0065b75d5e5fd8a5bc69617b9';
