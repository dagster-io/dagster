/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type AssetKeyInput = {
  path: Array<string>;
};

export type AssetsOverviewRootQueryVariables = Exact<{
  assetKey: Types.AssetKeyInput;
}>;

export type AssetsOverviewRootQuery = {
  __typename: 'Query';
  assetOrError:
    | {__typename: 'Asset'; id: string; key: {__typename: 'AssetKey'; path: Array<string>}}
    | {__typename: 'AssetNotFoundError'};
};

export const AssetsOverviewRootQueryVersion = '77ab0417c979b92c9ec01cd76a0f49b59f5b8ce7af775cab7e9b3e57b7871f7d';
