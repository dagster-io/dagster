/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type QueueDaemonStatusQueryVariables = Exact<{[key: string]: never}>;

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
