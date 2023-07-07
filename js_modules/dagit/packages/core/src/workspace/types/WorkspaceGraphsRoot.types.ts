// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type WorkspaceGraphsQueryVariables = Types.Exact<{
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
