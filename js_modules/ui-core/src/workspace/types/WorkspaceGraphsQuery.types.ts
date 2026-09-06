/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RepositorySelector = {
  repositoryLocationName: string;
  repositoryName: string;
};

export type RepositoryGraphsFragment = {
  __typename: 'Repository';
  id: string;
  usedSolids: Array<{
    __typename: 'UsedSolid';
    definition:
      | {
          __typename: 'CompositeSolidDefinition';
          id: string;
          name: string;
          description: string | null;
        }
      | {__typename: 'SolidDefinition'};
    invocations: Array<{
      __typename: 'NodeInvocationSite';
      pipeline: {__typename: 'Pipeline'; id: string; name: string};
      solidHandle: {__typename: 'SolidHandle'; handleID: string};
    }>;
  }>;
  pipelines: Array<{
    __typename: 'Pipeline';
    id: string;
    name: string;
    isJob: boolean;
    graphName: string;
  }>;
};

export type WorkspaceGraphsQueryVariables = Exact<{
  selector: Types.RepositorySelector;
}>;

export type WorkspaceGraphsQuery = {
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
        usedSolids: Array<{
          __typename: 'UsedSolid';
          definition:
            | {
                __typename: 'CompositeSolidDefinition';
                id: string;
                name: string;
                description: string | null;
              }
            | {__typename: 'SolidDefinition'};
          invocations: Array<{
            __typename: 'NodeInvocationSite';
            pipeline: {__typename: 'Pipeline'; id: string; name: string};
            solidHandle: {__typename: 'SolidHandle'; handleID: string};
          }>;
        }>;
        pipelines: Array<{
          __typename: 'Pipeline';
          id: string;
          name: string;
          isJob: boolean;
          graphName: string;
        }>;
      }
    | {__typename: 'RepositoryNotFoundError'};
};

export const WorkspaceGraphsQueryVersion = 'ccbef870f327b56beb0d781a476c8afbbc22ff2621181c8576861daaf7667ecf';
