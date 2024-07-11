// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetsOverviewRootQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
}>;

export type AssetsOverviewRootQuery = {
  __typename: 'Query';
  assetOrError:
    | {__typename: 'Asset'; id: string; key: {__typename: 'AssetKey'; path: Array<string>}}
    | {__typename: 'AssetNotFoundError'};
};
