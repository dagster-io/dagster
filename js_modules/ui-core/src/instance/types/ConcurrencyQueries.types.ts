/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ExecutionTag = {
  key: string;
  value: string;
};

export type RunStatus =
  | 'CANCELED'
  | 'CANCELING'
  | 'FAILURE'
  | 'MANAGED'
  | 'NOT_STARTED'
  | 'QUEUED'
  | 'STARTED'
  | 'STARTING'
  | 'SUCCESS';

export type RunsFilter = {
  createdAfter?: number | null | undefined;
  createdBefore?: number | null | undefined;
  mode?: string | null | undefined;
  pipelineName?: string | null | undefined;
  runIds?: Array<string | null | undefined> | null | undefined;
  snapshotId?: string | null | undefined;
  statuses?: Array<RunStatus> | null | undefined;
  tags?: Array<ExecutionTag> | null | undefined;
  updatedAfter?: number | null | undefined;
  updatedBefore?: number | null | undefined;
};

export type SetConcurrencyLimitMutationVariables = Exact<{
  concurrencyKey: string;
  limit: number;
}>;

export type SetConcurrencyLimitMutation = {__typename: 'Mutation'; setConcurrencyLimit: boolean};

export type DeleteConcurrencyLimitMutationVariables = Exact<{
  concurrencyKey: string;
}>;

export type DeleteConcurrencyLimitMutation = {
  __typename: 'Mutation';
  deleteConcurrencyLimit: boolean;
};

export type FreeConcurrencySlotsMutationVariables = Exact<{
  runId: string;
  stepKey?: string | null | undefined;
}>;

export type FreeConcurrencySlotsMutation = {__typename: 'Mutation'; freeConcurrencySlots: boolean};

export type RunsForConcurrencyKeyQueryVariables = Exact<{
  filter?: Types.RunsFilter | null | undefined;
  limit?: number | null | undefined;
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

export const RunsForConcurrencyKeyQueryVersion = '35ebd16622a13c6aaa35577c7694bf8ffdeb16921b46c6040a407bb3095eaf75';

export const DeleteVersion = '3c61c79b99122910e754a8863e80dc5ed479a0c23cc1a9d9878d91e603fc0dfe';
