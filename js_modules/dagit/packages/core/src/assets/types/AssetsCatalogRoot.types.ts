// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetsCatalogRootQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
}>;

export type AssetsCatalogRootQuery = {
  __typename: 'Query';
  assetOrError:
    | {__typename: 'Asset'; id: string; key: {__typename: 'AssetKey'; path: Array<string>}}
    | {__typename: 'AssetNotFoundError'};
};
