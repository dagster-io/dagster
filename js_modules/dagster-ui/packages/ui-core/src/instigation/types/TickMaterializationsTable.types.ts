// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetGroupAndLocationQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
}>;

export type AssetGroupAndLocationQuery = {
  __typename: 'Query';
  assetOrError:
    | {
        __typename: 'Asset';
        id: string;
        definition: {
          __typename: 'AssetNode';
          id: string;
          groupName: string;
          repository: {
            __typename: 'Repository';
            id: string;
            name: string;
            location: {__typename: 'RepositoryLocation'; id: string; name: string};
          };
        } | null;
      }
    | {__typename: 'AssetNotFoundError'};
};

export const AssetGroupAndLocationQueryVersion = '584b27ecda9ff883e92f2d8858520a543ea0be07d39e1b4c0fc5d802231bb602';
