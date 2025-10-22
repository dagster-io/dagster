// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type JobPermissionsQueryVariables = Types.Exact<{
  selector: Types.PipelineSelector;
}>;

export type JobPermissionsQuery = {
  __typename: 'Query';
  pipelineOrError:
    | {__typename: 'InvalidSubsetError'}
    | {
        __typename: 'Pipeline';
        id: string;
        hasLaunchExecutionPermission: boolean;
        hasLaunchReexecutionPermission: boolean;
      }
    | {__typename: 'PipelineNotFoundError'}
    | {__typename: 'PythonError'};
};

export const JobPermissionsQueryVersion = 'a9afe6f762bb3b4222b01eae07c25df6722e6485806ecc81260d8f679bb5e600';
