// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type ResumeBackfillMutationVariables = Types.Exact<{
  backfillId: Types.Scalars['String']['input'];
}>;

export type ResumeBackfillMutation = {
  __typename: 'Mutation';
  resumePartitionBackfill:
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
    | {__typename: 'ResumeBackfillSuccess'; backfillId: string}
    | {__typename: 'UnauthorizedError'; message: string};
};

export type LaunchPartitionBackfillMutationVariables = Types.Exact<{
  backfillParams: Types.LaunchBackfillParams;
}>;

export type LaunchPartitionBackfillMutation = {
  __typename: 'Mutation';
  launchPartitionBackfill:
    | {__typename: 'ConflictingExecutionParamsError'; message: string}
    | {__typename: 'InvalidOutputError'; stepKey: string; invalidOutputName: string}
    | {__typename: 'InvalidStepError'; invalidStepKey: string}
    | {__typename: 'InvalidSubsetError'}
    | {__typename: 'LaunchBackfillSuccess'; backfillId: string}
    | {__typename: 'NoModeProvidedError'}
    | {__typename: 'PartitionKeyNotFoundError'; message: string}
    | {__typename: 'PartitionSetNotFoundError'; message: string}
    | {__typename: 'PipelineNotFoundError'; message: string}
    | {__typename: 'PresetNotFoundError'; message: string}
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
        __typename: 'RunConfigValidationInvalid';
        pipelineName: string;
        errors: Array<
          | {
              __typename: 'FieldNotDefinedConfigError';
              message: string;
              path: Array<string>;
              reason: Types.EvaluationErrorReason;
            }
          | {
              __typename: 'FieldsNotDefinedConfigError';
              message: string;
              path: Array<string>;
              reason: Types.EvaluationErrorReason;
            }
          | {
              __typename: 'MissingFieldConfigError';
              message: string;
              path: Array<string>;
              reason: Types.EvaluationErrorReason;
            }
          | {
              __typename: 'MissingFieldsConfigError';
              message: string;
              path: Array<string>;
              reason: Types.EvaluationErrorReason;
            }
          | {
              __typename: 'RuntimeMismatchConfigError';
              message: string;
              path: Array<string>;
              reason: Types.EvaluationErrorReason;
            }
          | {
              __typename: 'SelectorTypeConfigError';
              message: string;
              path: Array<string>;
              reason: Types.EvaluationErrorReason;
            }
        >;
      }
    | {__typename: 'RunConflict'; message: string}
    | {__typename: 'UnauthorizedError'; message: string};
};

export const LaunchPartitionBackfillVersion = '832569ca3895aab07a2ff92616e28eaf2590357c3ab5e1cd8761da4da5f10697';
