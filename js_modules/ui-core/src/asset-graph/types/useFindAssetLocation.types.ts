// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetForNavigationQueryVariables = Types.Exact<{
  key: Types.AssetKeyInput;
}>;

export type AssetForNavigationQuery = {
  __typename: 'Query';
  assetOrError:
    | {
        __typename: 'Asset';
        id: string;
        definition: {
          __typename: 'AssetNode';
          id: string;
          opNames: Array<string>;
          jobNames: Array<string>;
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

export const AssetForNavigationQueryVersion = 'eb695ab88044ddd7068ea0dc1e2482eaba1fcb11b83de11050ff52f55e83ed3d';
