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
  runId: Types.Scalars['String'];
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
  runId: Types.Scalars['String'];
  terminatePolicy?: Types.InputMaybe<Types.TerminateRunPolicy>;
}>;

export type TerminateMutation = {
  __typename: 'Mutation';
  terminatePipelineExecution:
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
    | {__typename: 'UnauthorizedError'; message: string};
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
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
};
