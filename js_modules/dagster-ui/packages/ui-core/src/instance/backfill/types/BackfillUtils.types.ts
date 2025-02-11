// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

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
    | {__typename: 'PartitionKeysNotFoundError'; message: string}
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

export const LaunchPartitionBackfillVersion = '07bf7523e7b8696598d621aad89a48f25e173a3955ab84dd60a745c21aff2d9b';
