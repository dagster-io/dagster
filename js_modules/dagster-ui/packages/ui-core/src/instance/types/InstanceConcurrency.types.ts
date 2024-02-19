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

export type RunQueueConfigFragment = {
  __typename: 'RunQueueConfig';
  maxConcurrentRuns: number;
  tagConcurrencyLimitsYaml: string | null;
};

export type InstanceConcurrencyLimitsQueryVariables = Types.Exact<{[key: string]: never}>;

export type InstanceConcurrencyLimitsQuery = {
  __typename: 'Query';
  instance: {
    __typename: 'Instance';
    id: string;
    info: string | null;
    supportsConcurrencyLimits: boolean;
    runQueuingSupported: boolean;
    minConcurrencyLimitValue: number;
    maxConcurrencyLimitValue: number;
    runQueueConfig: {
      __typename: 'RunQueueConfig';
      maxConcurrentRuns: number;
      tagConcurrencyLimitsYaml: string | null;
    } | null;
    concurrencyLimits: Array<{
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
    }>;
  };
};

export type SetConcurrencyLimitMutationVariables = Types.Exact<{
  concurrencyKey: Types.Scalars['String'];
  limit: Types.Scalars['Int'];
}>;

export type SetConcurrencyLimitMutation = {__typename: 'Mutation'; setConcurrencyLimit: boolean};

export type DeleteConcurrencyLimitMutationVariables = Types.Exact<{
  concurrencyKey: Types.Scalars['String'];
}>;

export type DeleteConcurrencyLimitMutation = {
  __typename: 'Mutation';
  deleteConcurrencyLimit: boolean;
};

export type FreeConcurrencySlotsMutationVariables = Types.Exact<{
  runId: Types.Scalars['String'];
  stepKey?: Types.InputMaybe<Types.Scalars['String']>;
}>;

export type FreeConcurrencySlotsMutation = {__typename: 'Mutation'; freeConcurrencySlots: boolean};

export type ConcurrencyKeyDetailsQueryVariables = Types.Exact<{
  concurrencyKey: Types.Scalars['String'];
}>;

export type ConcurrencyKeyDetailsQuery = {
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

export type RunsForConcurrencyKeyQueryVariables = Types.Exact<{
  filter?: Types.InputMaybe<Types.RunsFilter>;
  limit?: Types.InputMaybe<Types.Scalars['Int']>;
}>;

export type RunsForConcurrencyKeyQuery = {
  __typename: 'Query';
  pipelineRunsOrError:
    | {__typename: 'InvalidPipelineRunsFilterError'}
    | {__typename: 'PythonError'}
    | {
        __typename: 'Runs';
        results: Array<{__typename: 'Run'; id: string; status: Types.RunStatus}>;
      };
};
