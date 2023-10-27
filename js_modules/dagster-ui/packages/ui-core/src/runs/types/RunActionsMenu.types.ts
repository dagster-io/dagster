// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type PipelineEnvironmentQueryVariables = Types.Exact<{
  runId: Types.Scalars['ID'];
}>;

export type PipelineEnvironmentQuery = {
  __typename: 'Query';
  pipelineRunOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Run';
        id: string;
        pipelineName: string;
        pipelineSnapshotId: string | null;
        runConfigYaml: string;
        parentPipelineSnapshotId: string | null;
        repositoryOrigin: {
          __typename: 'RepositoryOrigin';
          id: string;
          repositoryName: string;
          repositoryLocationName: string;
        } | null;
      }
    | {__typename: 'RunNotFoundError'};
};
