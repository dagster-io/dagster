// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RepositoryLocationStatusQueryVariables = Types.Exact<{[key: string]: never}>;

export type RepositoryLocationStatusQuery = {
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
          loadStatus: Types.RepositoryLocationLoadStatus;
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
                repositories: Array<{
                  __typename: 'Repository';
                  id: string;
                  name: string;
                  pipelines: Array<{__typename: 'Pipeline'; id: string; name: string}>;
                }>;
              }
            | null;
        }>;
      };
};

export type ReloadWorkspaceMutationVariables = Types.Exact<{[key: string]: never}>;

export type ReloadWorkspaceMutation = {
  __typename: 'Mutation';
  reloadWorkspace:
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
    | {__typename: 'UnauthorizedError'; message: string}
    | {
        __typename: 'Workspace';
        id: string;
        locationEntries: Array<{
          __typename: 'WorkspaceLocationEntry';
          name: string;
          id: string;
          loadStatus: Types.RepositoryLocationLoadStatus;
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
                repositories: Array<{
                  __typename: 'Repository';
                  id: string;
                  name: string;
                  pipelines: Array<{__typename: 'Pipeline'; id: string; name: string}>;
                }>;
              }
            | null;
        }>;
      };
};

export type ReloadRepositoryLocationMutationVariables = Types.Exact<{
  location: Types.Scalars['String'];
}>;

export type ReloadRepositoryLocationMutation = {
  __typename: 'Mutation';
  reloadRepositoryLocation:
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
    | {__typename: 'ReloadNotSupported'; message: string}
    | {__typename: 'RepositoryLocationNotFound'; message: string}
    | {__typename: 'UnauthorizedError'; message: string}
    | {
        __typename: 'WorkspaceLocationEntry';
        id: string;
        loadStatus: Types.RepositoryLocationLoadStatus;
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
          | {__typename: 'RepositoryLocation'; id: string}
          | null;
      };
};
