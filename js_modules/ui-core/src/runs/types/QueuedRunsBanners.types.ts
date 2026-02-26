// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type QueueDaemonStatusQueryVariables = Types.Exact<{[key: string]: never}>;

export type QueueDaemonStatusQuery = {
  __typename: 'Query';
  instance: {
    __typename: 'Instance';
    id: string;
    daemonHealth: {
      __typename: 'DaemonHealth';
      id: string;
      daemonStatus: {
        __typename: 'DaemonStatus';
        id: string;
        daemonType: string;
        healthy: boolean | null;
        required: boolean;
      };
    };
  };
};

export const QueueDaemonStatusQueryVersion = 'aa51c596ee907346e60e2fe173bba10ae2ead067d45109225a2cd400a2278841';
