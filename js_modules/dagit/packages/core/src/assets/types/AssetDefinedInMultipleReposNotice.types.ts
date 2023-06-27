// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetDefinitionCollisionQueryVariables = Types.Exact<{
  assetKeys: Array<Types.AssetKeyInput> | Types.AssetKeyInput;
}>;

export type AssetDefinitionCollisionQuery = {
  __typename: 'Query';
  assetNodeDefinitionCollisions: Array<{
    __typename: 'AssetNodeDefinitionCollision';
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
    repositories: Array<{
      __typename: 'Repository';
      id: string;
      name: string;
      location: {__typename: 'RepositoryLocation'; id: string; name: string};
    }>;
  }>;
};
