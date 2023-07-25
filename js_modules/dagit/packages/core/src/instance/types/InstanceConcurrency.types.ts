// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ConcurrencyLimitFragment = {
  __typename: 'ConcurrencyKeyInfo';
  concurrencyKey: string;
  slotCount: number;
  activeRunIds: Array<string>;
  activeSlotCount: number;
};

export type InstanceConcurrencyLimitsQueryVariables = Types.Exact<{[key: string]: never}>;

export type InstanceConcurrencyLimitsQuery = {
  __typename: 'Query';
  instance: {
    __typename: 'Instance';
    id: string;
    concurrencyLimits: Array<{
      __typename: 'ConcurrencyKeyInfo';
      concurrencyKey: string;
      slotCount: number;
      activeRunIds: Array<string>;
      activeSlotCount: number;
    }>;
  };
};

export type SetConcurrencyLimitMutationVariables = Types.Exact<{
  concurrencyKey: Types.Scalars['String'];
  limit: Types.Scalars['Int'];
}>;

export type SetConcurrencyLimitMutation = {__typename: 'Mutation'; setConcurrencyLimit: boolean};

export type FreeConcurrencySlotsForRunMutationVariables = Types.Exact<{
  runId: Types.Scalars['String'];
}>;

export type FreeConcurrencySlotsForRunMutation = {
  __typename: 'Mutation';
  freeConcurrencySlotsForRun: boolean;
};

export type RunsForConcurrencyKeyQueryVariables = Types.Exact<{
  filter?: Types.InputMaybe<Types.RunsFilter>;
  limit?: Types.InputMaybe<Types.Scalars['Int']>;
}>;

export type RunsForConcurrencyKeyQuery = {
  __typename: 'Query';
  pipelineRunsOrError:
    | {__typename: 'InvalidPipelineRunsFilterError'}
    | {
        __typename: 'PythonError';
        message: string;
        stack: Array<string>;
        errorChain: Array<{
          __typename: 'ErrorChainLink';
          isExplicitLink: boolean;
          error: {__typename: 'PythonError'; message: string; stack: Array<string>};
        }>;
      }
    | {
        __typename: 'Runs';
        results: Array<{
          __typename: 'Run';
          id: string;
          status: Types.RunStatus;
          stepKeysToExecute: Array<string> | null;
          canTerminate: boolean;
          hasReExecutePermission: boolean;
          hasTerminatePermission: boolean;
          hasDeletePermission: boolean;
          mode: string;
          rootRunId: string | null;
          parentRunId: string | null;
          pipelineSnapshotId: string | null;
          pipelineName: string;
          solidSelection: Array<string> | null;
          startTime: number | null;
          endTime: number | null;
          updateTime: number | null;
          repositoryOrigin: {
            __typename: 'RepositoryOrigin';
            id: string;
            repositoryName: string;
            repositoryLocationName: string;
          } | null;
          assetSelection: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
          tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
        }>;
      };
};
