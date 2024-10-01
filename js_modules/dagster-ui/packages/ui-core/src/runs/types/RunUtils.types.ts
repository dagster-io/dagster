// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type LaunchPipelineExecutionMutationVariables = Types.Exact<{
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

export type DeleteMutationVariables = Types.Exact<{
  runId: Types.Scalars['String']['input'];
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

export type TerminateMutationVariables = Types.Exact<{
  runIds: Array<Types.Scalars['String']['input']> | Types.Scalars['String']['input'];
  terminatePolicy?: Types.InputMaybe<Types.TerminateRunPolicy>;
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

export type LaunchPipelineReexecutionMutationVariables = Types.Exact<{
  executionParams?: Types.InputMaybe<Types.ExecutionParams>;
  reexecutionParams?: Types.InputMaybe<Types.ReexecutionParams>;
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

export const DeleteVersion = '3c61c79b99122910e754a8863e80dc5ed479a0c23cc1a9d9878d91e603fc0dfe';

export const TerminateVersion = '67acf403eb320a93c9a9aa07f675a1557e0887d499cd5598f1d5ff360afc15c0';

export const LaunchPipelineReexecutionVersion = 'd21e4ecaf3d1d163c4772f1d847dbdcbdaa9a40e6de0808a064ae767adf0c311';
