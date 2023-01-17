// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RepositoryAssetsListQueryVariables = Types.Exact<{
  repositorySelector: Types.RepositorySelector;
}>;

export type RepositoryAssetsListQuery = {
  __typename: 'DagitQuery';
  repositoryOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Repository';
        id: string;
        assetNodes: Array<{
          __typename: 'AssetNode';
          id: string;
          opNames: Array<string>;
          description: string | null;
          assetKey: {__typename: 'AssetKey'; path: Array<string>};
          repository: {
            __typename: 'Repository';
            id: string;
            name: string;
            location: {__typename: 'RepositoryLocation'; id: string; name: string};
          };
        }>;
      }
    | {__typename: 'RepositoryNotFoundError'; message: string};
};
