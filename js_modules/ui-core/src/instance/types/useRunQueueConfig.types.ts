/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type InstanceRunQueueConfigQueryVariables = Exact<{[key: string]: never}>;

export type InstanceRunQueueConfigQuery = {
  __typename: 'Query';
  instance: {
    __typename: 'Instance';
    id: string;
    hasInfo: boolean;
    runQueueConfig: {
      __typename: 'RunQueueConfig';
      maxConcurrentRuns: number;
      tagConcurrencyLimitsYaml: string | null;
      isOpConcurrencyAware: boolean | null;
      maxConcurrentRunsAllBranchDeployments: number | null;
    } | null;
  };
};

export const InstanceRunQueueConfigVersion = '5c8118738d025aa9b56439d1a142077acfc3dfbade689f3cae4d34100f740233';
