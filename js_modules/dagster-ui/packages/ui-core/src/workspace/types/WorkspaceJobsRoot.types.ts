// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type WorkspaceJobsQueryVariables = Types.Exact<{
  selector: Types.RepositorySelector;
}>;

export type WorkspaceJobsQuery = {
  __typename: 'Query';
  repositoryOrError:
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
        __typename: 'Repository';
        id: string;
        name: string;
        pipelines: Array<{__typename: 'Pipeline'; id: string; name: string; isJob: boolean}>;
      }
    | {__typename: 'RepositoryNotFoundError'};
};

export const WorkspaceJobsQueryVersion = '637f616d6d4eba194cf80bbb292f579f864d3b16aeb0b40cdf108d8100ba9b1c';
