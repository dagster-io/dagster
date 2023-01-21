// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RepositoryGraphsListQueryVariables = Types.Exact<{
  repositorySelector: Types.RepositorySelector;
}>;

export type RepositoryGraphsListQuery = {
  __typename: 'DagitQuery';
  repositoryOrError:
    | {__typename: 'PythonError'}
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
          description: string | null;
          name: string;
          isJob: boolean;
          graphName: string;
        }>;
      }
    | {__typename: 'RepositoryNotFoundError'; message: string};
};
