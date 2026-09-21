/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type SingleConcurrencyKeyQueryVariables = Exact<{
  concurrencyKey: string;
}>;

export type SingleConcurrencyKeyQuery = {
  __typename: 'Query';
  instance: {
    __typename: 'Instance';
    id: string;
    concurrencyLimit: {
      __typename: 'ConcurrencyKeyInfo';
      concurrencyKey: string;
      slotCount: number;
      claimedSlots: Array<{__typename: 'ClaimedConcurrencySlot'; runId: string; stepKey: string}>;
      pendingSteps: Array<{
        __typename: 'PendingConcurrencyStep';
        runId: string;
        stepKey: string;
        enqueuedTimestamp: number;
        assignedTimestamp: number | null;
        priority: number | null;
      }>;
    };
  };
};

export const SingleConcurrencyKeyQueryVersion = 'fd72bd62ac87f3c72ec589610c7c52398643740f1f2904b04e1e293b08daf763';
