/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type ExecutionTag = {
  key: string;
  value: string;
};

export type ReexecutionParams = {
  extraTags?: Array<ExecutionTag> | null | undefined;
  parentRunId: string;
  strategy: ReexecutionStrategy;
  useParentRunTags?: boolean | null | undefined;
};

export type ReexecutionStrategy = 'ALL_STEPS' | 'FROM_ASSET_FAILURE' | 'FROM_FAILURE';

export type ReexecuteBackfillMutationVariables = Exact<{
  reexecutionParams: Types.ReexecutionParams;
}>;

export type ReexecuteBackfillMutation = {
  __typename: 'Mutation';
  reexecutePartitionBackfill:
    | {__typename: 'ConflictingExecutionParamsError'}
    | {__typename: 'InvalidOutputError'}
    | {__typename: 'InvalidStepError'}
    | {__typename: 'InvalidSubsetError'}
    | {__typename: 'LaunchBackfillSuccess'; backfillId: string}
    | {__typename: 'NoModeProvidedError'}
    | {__typename: 'PartitionKeysNotFoundError'}
    | {__typename: 'PartitionSetNotFoundError'}
    | {__typename: 'PipelineNotFoundError'}
    | {__typename: 'PresetNotFoundError'}
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
    | {__typename: 'RunConfigValidationInvalid'}
    | {__typename: 'RunConflict'}
    | {__typename: 'UnauthorizedError'; message: string};
};
