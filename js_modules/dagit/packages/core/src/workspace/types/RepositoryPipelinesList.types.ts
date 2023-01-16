// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RepositoryPipelinesListQueryVariables = Types.Exact<{
  repositorySelector: Types.RepositorySelector;
}>;

export type RepositoryPipelinesListQuery = {
  __typename: 'DagitQuery';
  repositoryOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Repository';
        id: string;
        pipelines: Array<{
          __typename: 'Pipeline';
          id: string;
          description: string | null;
          isJob: boolean;
          name: string;
          modes: Array<{__typename: 'Mode'; id: string; name: string}>;
          runs: Array<{
            __typename: 'Run';
            id: string;
            mode: string;
            runId: string;
            status: Types.RunStatus;
          }>;
          schedules: Array<{__typename: 'Schedule'; id: string; name: string; mode: string}>;
          sensors: Array<{
            __typename: 'Sensor';
            id: string;
            name: string;
            targets: Array<{__typename: 'Target'; mode: string; pipelineName: string}> | null;
          }>;
        }>;
      }
    | {__typename: 'RepositoryNotFoundError'; message: string};
};
