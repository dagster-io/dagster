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
