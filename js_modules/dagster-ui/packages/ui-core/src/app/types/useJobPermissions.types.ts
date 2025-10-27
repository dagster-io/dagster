// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type JobPermissionsQueryVariables = Types.Exact<{
  selector: Types.PipelineSelector;
}>;

export type JobPermissionsQuery = {
  __typename: 'Query';
  pipelineOrError:
    | {__typename: 'InvalidSubsetError'; message: string}
    | {
        __typename: 'Pipeline';
        id: string;
        hasLaunchExecutionPermission: boolean;
        hasLaunchReexecutionPermission: boolean;
      }
    | {__typename: 'PipelineNotFoundError'; message: string}
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

export const JobPermissionsQueryVersion = 'bc1633194c82d8531b5bb9b2b482ce70123949e106dd38463a3a0575f61788cd';
