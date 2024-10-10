// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type OverviewJobsQueryVariables = Types.Exact<{[key: string]: never}>;

export type OverviewJobsQuery = {
  __typename: 'Query';
  workspaceOrError:
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
        __typename: 'Workspace';
        id: string;
        locationEntries: Array<{
          __typename: 'WorkspaceLocationEntry';
          id: string;
          locationOrLoadError:
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
                __typename: 'RepositoryLocation';
                id: string;
                name: string;
                repositories: Array<{
                  __typename: 'Repository';
                  id: string;
                  name: string;
                  pipelines: Array<{
                    __typename: 'Pipeline';
                    id: string;
                    name: string;
                    isJob: boolean;
                    tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
                  }>;
                }>;
              }
            | null;
        }>;
      };
};

export const OverviewJobsQueryVersion = '7de05cca36088c46f8dbd3f995d643fc7e79f240eae0bc614bcf68a0729fe7d9';
