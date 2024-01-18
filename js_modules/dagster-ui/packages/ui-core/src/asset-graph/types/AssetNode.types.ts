// Generated GraphQL types, do not edit manually.
import * as Types from '../../graphql/types';

export type AssetNodeFragment = {
  __typename: 'AssetNode';
  id: string;
  graphName: string | null;
  hasMaterializePermission: boolean;
  jobNames: Array<string>;
  opNames: Array<string>;
  opVersion: string | null;
  description: string | null;
  computeKind: string | null;
  isPartitioned: boolean;
  isObservable: boolean;
  isSource: boolean;
  assetKey: {__typename: 'AssetKey'; path: Array<string>};
};

export type AssetNodeKeyFragment = {__typename: 'AssetKey'; path: Array<string>};
