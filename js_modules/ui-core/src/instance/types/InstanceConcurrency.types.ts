/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunQueueConfigFragment = {
  __typename: 'RunQueueConfig';
  maxConcurrentRuns: number;
  tagConcurrencyLimitsYaml: string | null;
};

export type InstanceConcurrencyLimitsQueryVariables = Exact<{[key: string]: never}>;

export type InstanceConcurrencyLimitsQuery = {
  __typename: 'Query';
  instance: {
    __typename: 'Instance';
    id: string;
    supportsConcurrencyLimits: boolean;
    runQueuingSupported: boolean;
    minConcurrencyLimitValue: number;
    maxConcurrencyLimitValue: number;
    runQueueConfig: {
      __typename: 'RunQueueConfig';
      maxConcurrentRuns: number;
      tagConcurrencyLimitsYaml: string | null;
    } | null;
    concurrencyLimits: Array<{__typename: 'ConcurrencyKeyInfo'; concurrencyKey: string}>;
  };
};

export const InstanceConcurrencyLimitsQueryVersion = 'bd8c406b16c8dce571454c6504becc886bee182e3a6aacdc68034f54eeb05b79';
