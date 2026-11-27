/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type AssetKeyInput = {
  path: Array<string>;
};

export type EvaluationErrorReason =
  | 'FIELDS_NOT_DEFINED'
  | 'FIELD_NOT_DEFINED'
  | 'MISSING_REQUIRED_FIELD'
  | 'MISSING_REQUIRED_FIELDS'
  | 'RUNTIME_TYPE_MISMATCH'
  | 'SELECTOR_FIELD_ERROR';

export type ExecutionTag = {
  key: string;
  value: string;
};

export type LaunchBackfillParams = {
  allPartitions?: boolean | null | undefined;
  assetSelection?: Array<AssetKeyInput> | null | undefined;
  description?: string | null | undefined;
  forceSynchronousSubmission?: boolean | null | undefined;
  fromFailure?: boolean | null | undefined;
  partitionNames?: Array<string> | null | undefined;
  partitionsByAssets?: Array<PartitionsByAssetSelector | null | undefined> | null | undefined;
  reexecutionSteps?: Array<string> | null | undefined;
  runConfigData?: any;
  selector?: PartitionSetSelector | null | undefined;
  tags?: Array<ExecutionTag> | null | undefined;
  title?: string | null | undefined;
};

export type PartitionRangeSelector = {
  end: string;
  start: string;
};

export type PartitionSetSelector = {
  partitionSetName: string;
  repositorySelector: RepositorySelector;
};

export type PartitionsByAssetSelector = {
  assetKey: AssetKeyInput;
  partitions?: PartitionsSelector | null | undefined;
};

export type PartitionsSelector = {
  range?: PartitionRangeSelector | null | undefined;
  ranges?: Array<PartitionRangeSelector> | null | undefined;
};

export type RepositorySelector = {
  repositoryLocationName: string;
  repositoryName: string;
};

export type LaunchPartitionBackfillMutationVariables = Exact<{
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
