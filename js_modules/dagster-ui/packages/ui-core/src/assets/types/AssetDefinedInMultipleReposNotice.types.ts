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

export const AssetDefinitionCollisionQueryVersion = '84027ea05480797a69eb150ce07ac7dfd40d6007a8107f90a6c558cf3a2662f5';
