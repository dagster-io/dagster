/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type UnderlyingOpsAssetNodeFragment = {
  __typename: 'AssetNode';
  id: string;
  graphName: string | null;
  opNames: Array<string>;
  jobNames: Array<string>;
  assetKey: {__typename: 'AssetKey'; path: Array<string>};
};
