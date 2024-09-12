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

export const AssetsOverviewRootQueryVersion = '77ab0417c979b92c9ec01cd76a0f49b59f5b8ce7af775cab7e9b3e57b7871f7d';
