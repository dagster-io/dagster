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
