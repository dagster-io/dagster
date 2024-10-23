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
  location: Types.Scalars['String']['input'];
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

export const RepositoryLocationStatusQueryVersion = '7129557ca993e0638a147e30c6fe3bdff04a929d4e6775c3e4e5dc9fa3c88d94';

export const ReloadWorkspaceMutationVersion = '763808cb236e2d60a426cd891a4f60efd6851a755345d4a3ef019549f35e0a5e';

export const ReloadRepositoryLocationMutationVersion = '19f0c7c1764ac7327424133d498295b6417cb00ef06d88f30a458a7d33926e26';
