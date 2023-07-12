// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type WorkspaceAssetsQueryVariables = Types.Exact<{
  selector: Types.RepositorySelector;
}>;

export type WorkspaceAssetsQuery = {
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
        assetNodes: Array<{
          __typename: 'AssetNode';
          id: string;
          groupName: string | null;
          opNames: Array<string>;
          isSource: boolean;
          isObservable: boolean;
          computeKind: string | null;
          hasMaterializePermission: boolean;
          description: string | null;
          assetKey: {__typename: 'AssetKey'; path: Array<string>};
          partitionDefinition: {__typename: 'PartitionDefinition'; description: string} | null;
          repository: {
            __typename: 'Repository';
            id: string;
            name: string;
            location: {__typename: 'RepositoryLocation'; id: string; name: string};
          };
        }>;
      }
    | {__typename: 'RepositoryNotFoundError'};
};
