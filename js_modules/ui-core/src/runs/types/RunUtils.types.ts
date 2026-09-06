/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetCheckHandleInput = {
  assetKey: AssetKeyInput;
  name: string;
};

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

export type ExecutionMetadata = {
  parentRunId?: string | null | undefined;
  rootRunId?: string | null | undefined;
  tags?: Array<ExecutionTag> | null | undefined;
};

export type ExecutionParams = {
  executionMetadata?: ExecutionMetadata | null | undefined;
  mode?: string | null | undefined;
  preset?: string | null | undefined;
  runConfigData?: any;
  selector: JobOrPipelineSelector;
  stepKeys?: Array<string> | null | undefined;
};

export type ExecutionTag = {
  key: string;
  value: string;
};

export type JobOrPipelineSelector = {
  assetCheckSelection?: Array<AssetCheckHandleInput> | null | undefined;
  assetSelection?: Array<AssetKeyInput> | null | undefined;
  jobName?: string | null | undefined;
  pipelineName?: string | null | undefined;
  repositoryLocationName: string;
  repositoryName: string;
  solidSelection?: Array<string> | null | undefined;
};

export type ReexecutionParams = {
  extraTags?: Array<ExecutionTag> | null | undefined;
  parentRunId: string;
  strategy: ReexecutionStrategy;
  useParentRunTags?: boolean | null | undefined;
};

export type ReexecutionStrategy = 'ALL_STEPS' | 'FROM_ASSET_FAILURE' | 'FROM_FAILURE';

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

export type TerminateRunPolicy = 'MARK_AS_CANCELED_IMMEDIATELY' | 'SAFE_TERMINATE';

export type LaunchPipelineExecutionMutationVariables = Exact<{
  executionParams: Types.ExecutionParams;
}>;

export type LaunchPipelineExecutionMutation = {
  __typename: 'Mutation';
  launchPipelineExecution:
    | {__typename: 'ConflictingExecutionParamsError'}
    | {__typename: 'InvalidOutputError'}
    | {__typename: 'InvalidStepError'}
    | {__typename: 'InvalidSubsetError'; message: string}
    | {__typename: 'LaunchRunSuccess'; run: {__typename: 'Run'; id: string; pipelineName: string}}
    | {__typename: 'NoModeProvidedError'}
    | {__typename: 'PipelineNotFoundError'; message: string}
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
    | {
        __typename: 'RunConfigValidationInvalid';
        errors: Array<
          | {__typename: 'FieldNotDefinedConfigError'; message: string}
          | {__typename: 'FieldsNotDefinedConfigError'; message: string}
          | {__typename: 'MissingFieldConfigError'; message: string}
          | {__typename: 'MissingFieldsConfigError'; message: string}
          | {__typename: 'RuntimeMismatchConfigError'; message: string}
          | {__typename: 'SelectorTypeConfigError'; message: string}
        >;
      }
    | {__typename: 'RunConflict'}
    | {__typename: 'UnauthorizedError'};
};

export type LaunchMultipleRunsMutationVariables = Exact<{
  executionParamsList: Array<Types.ExecutionParams> | Types.ExecutionParams;
}>;

export type LaunchMultipleRunsMutation = {
  __typename: 'Mutation';
  launchMultipleRuns:
    | {
        __typename: 'LaunchMultipleRunsResult';
        launchMultipleRunsResult: Array<
          | {__typename: 'ConflictingExecutionParamsError'; message: string}
          | {__typename: 'InvalidOutputError'; stepKey: string; invalidOutputName: string}
          | {__typename: 'InvalidStepError'; invalidStepKey: string}
          | {__typename: 'InvalidSubsetError'}
          | {
              __typename: 'LaunchRunSuccess';
              run: {
                __typename: 'Run';
                id: string;
                status: Types.RunStatus;
                runConfigYaml: string;
                mode: string;
                resolvedOpSelection: Array<string> | null;
                pipeline:
                  | {__typename: 'PipelineSnapshot'; name: string}
                  | {__typename: 'UnknownPipeline'; name: string};
                tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
              };
            }
          | {__typename: 'NoModeProvidedError'}
          | {__typename: 'PipelineNotFoundError'; message: string; pipelineName: string}
          | {__typename: 'PresetNotFoundError'; preset: string; message: string}
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
          | {__typename: 'RunConflict'}
          | {__typename: 'UnauthorizedError'}
        >;
      }
    | {
        __typename: 'PythonError';
        message: string;
        stack: Array<string>;
        errorChain: Array<{
          __typename: 'ErrorChainLink';
          isExplicitLink: boolean;
          error: {__typename: 'PythonError'; message: string; stack: Array<string>};
        }>;
      };
};

export type DeleteMutationVariables = Exact<{
  runId: string;
}>;

export type DeleteMutation = {
  __typename: 'Mutation';
  deletePipelineRun:
    | {__typename: 'DeletePipelineRunSuccess'}
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
    | {__typename: 'RunNotFoundError'; message: string}
    | {__typename: 'UnauthorizedError'; message: string};
};

export type TerminateMutationVariables = Exact<{
  runIds: Array<string> | string;
  terminatePolicy?: Types.TerminateRunPolicy | null | undefined;
}>;

export type TerminateMutation = {
  __typename: 'Mutation';
  terminateRuns:
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
        __typename: 'TerminateRunsResult';
        terminateRunResults: Array<
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
          | {__typename: 'RunNotFoundError'; message: string}
          | {__typename: 'TerminateRunFailure'; message: string}
          | {
              __typename: 'TerminateRunSuccess';
              run: {__typename: 'Run'; id: string; canTerminate: boolean};
            }
          | {__typename: 'UnauthorizedError'; message: string}
        >;
      };
};

export type LaunchPipelineReexecutionMutationVariables = Exact<{
  executionParams?: Types.ExecutionParams | null | undefined;
  reexecutionParams?: Types.ReexecutionParams | null | undefined;
}>;

export type LaunchPipelineReexecutionMutation = {
  __typename: 'Mutation';
  launchPipelineReexecution:
    | {__typename: 'ConflictingExecutionParamsError'}
    | {__typename: 'InvalidOutputError'}
    | {__typename: 'InvalidStepError'}
    | {__typename: 'InvalidSubsetError'; message: string}
    | {
        __typename: 'LaunchRunSuccess';
        run: {
          __typename: 'Run';
          id: string;
          pipelineName: string;
          rootRunId: string | null;
          parentRunId: string | null;
        };
      }
    | {__typename: 'NoModeProvidedError'}
    | {__typename: 'PipelineNotFoundError'; message: string}
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
    | {
        __typename: 'RunConfigValidationInvalid';
        errors: Array<
          | {__typename: 'FieldNotDefinedConfigError'; message: string}
          | {__typename: 'FieldsNotDefinedConfigError'; message: string}
          | {__typename: 'MissingFieldConfigError'; message: string}
          | {__typename: 'MissingFieldsConfigError'; message: string}
          | {__typename: 'RuntimeMismatchConfigError'; message: string}
          | {__typename: 'SelectorTypeConfigError'; message: string}
        >;
      }
    | {__typename: 'RunConflict'}
    | {__typename: 'UnauthorizedError'};
};

export type RunTimeFragment = {
  __typename: 'Run';
  id: string;
  status: Types.RunStatus;
  creationTime: number;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
};

export const LaunchPipelineExecutionVersion = '292088c4a697aca6be1d3bbc0cfc45d8a13cdb2e75cfedc64b68c6245ea34f89';

export const LaunchMultipleRunsVersion = 'a56d9efdb35e71e0fd1744dd768129248943bc5b23e717458b82c46829661763';

export const DeleteVersion = '3c61c79b99122910e754a8863e80dc5ed479a0c23cc1a9d9878d91e603fc0dfe';

export const TerminateVersion = '67acf403eb320a93c9a9aa07f675a1557e0887d499cd5598f1d5ff360afc15c0';

export const LaunchPipelineReexecutionVersion = 'd21e4ecaf3d1d163c4772f1d847dbdcbdaa9a40e6de0808a064ae767adf0c311';
