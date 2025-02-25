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

export type SetConcurrencyLimitMutationVariables = Types.Exact<{
  concurrencyKey: Types.Scalars['String']['input'];
  limit: Types.Scalars['Int']['input'];
}>;

export type SetConcurrencyLimitMutation = {__typename: 'Mutation'; setConcurrencyLimit: boolean};

export type DeleteConcurrencyLimitMutationVariables = Types.Exact<{
  concurrencyKey: Types.Scalars['String']['input'];
}>;

export type DeleteConcurrencyLimitMutation = {
  __typename: 'Mutation';
  deleteConcurrencyLimit: boolean;
};

export type FreeConcurrencySlotsMutationVariables = Types.Exact<{
  runId: Types.Scalars['String']['input'];
  stepKey?: Types.InputMaybe<Types.Scalars['String']['input']>;
}>;

export type FreeConcurrencySlotsMutation = {__typename: 'Mutation'; freeConcurrencySlots: boolean};

export type ConcurrencyKeyDetailsQueryVariables = Types.Exact<{
  concurrencyKey: Types.Scalars['String']['input'];
}>;

export type ConcurrencyKeyDetailsQuery = {
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

export type RunsForConcurrencyKeyQueryVariables = Types.Exact<{
  filter?: Types.InputMaybe<Types.RunsFilter>;
  limit?: Types.InputMaybe<Types.Scalars['Int']['input']>;
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

export const SetConcurrencyLimitVersion = '758e6bfdb936dff3e4e38f8e1fb447548710a2b2c66fbcad9d4f264a10a61044';

export const DeleteConcurrencyLimitVersion = '03397142bc71bc17649f43dd17aabf4ea771436ebc4ee1cb40eff2c2848d7b4d';

export const FreeConcurrencySlotsVersion = '7363c435dba06ed2a4be96e1d9bf1f1f8d9c90533b80ff42896fe9d50879d60e';

export const ConcurrencyKeyDetailsQueryVersion = '4578bc70e20ae2324dd5b870dde4e2ffb85708c050dacdaa6741e2a7f67edf7d';

export const RunsForConcurrencyKeyQueryVersion = '35ebd16622a13c6aaa35577c7694bf8ffdeb16921b46c6040a407bb3095eaf75';

export const DeleteVersion = '3c61c79b99122910e754a8863e80dc5ed479a0c23cc1a9d9878d91e603fc0dfe';
