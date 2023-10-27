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
