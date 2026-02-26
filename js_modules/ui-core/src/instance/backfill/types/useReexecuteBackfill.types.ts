// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type ReexecuteBackfillMutationVariables = Types.Exact<{
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
