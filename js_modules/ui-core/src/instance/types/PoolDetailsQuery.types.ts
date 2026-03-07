// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ConcurrencyStepFragment = {
  __typename: 'PendingConcurrencyStep';
  runId: string;
  stepKey: string;
  enqueuedTimestamp: number;
  assignedTimestamp: number | null;
  priority: number | null;
};

export type ConcurrencyLimitFragment = {
  __typename: 'ConcurrencyKeyInfo';
  concurrencyKey: string;
  limit: number | null;
  slotCount: number;
  usingDefaultLimit: boolean | null;
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

export type PoolDetailsQueryVariables = Types.Exact<{
  pool: Types.Scalars['String']['input'];
}>;

export type PoolDetailsQuery = {
  __typename: 'Query';
  instance: {
    __typename: 'Instance';
    id: string;
    minConcurrencyLimitValue: number;
    maxConcurrencyLimitValue: number;
    runQueuingSupported: boolean;
    poolConfig: {
      __typename: 'PoolConfig';
      poolGranularity: string | null;
      defaultPoolLimit: number | null;
      opGranularityRunBuffer: number | null;
    } | null;
    concurrencyLimit: {
      __typename: 'ConcurrencyKeyInfo';
      concurrencyKey: string;
      limit: number | null;
      slotCount: number;
      usingDefaultLimit: boolean | null;
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

export const PoolDetailsQueryVersion = '0e59b6925f724d123c5ce6fc2d9d9a10160b73b16db1e81f54825020b51d644f';
