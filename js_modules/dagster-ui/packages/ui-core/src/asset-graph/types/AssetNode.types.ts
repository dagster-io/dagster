// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetNodeFragment = {
  __typename: 'AssetNode';
  id: string;
  graphName: string | null;
  hasMaterializePermission: boolean;
  jobNames: Array<string>;
  changedReasons: Array<Types.ChangeReason>;
  opNames: Array<string>;
  opVersion: string | null;
  description: string | null;
  computeKind: string | null;
  isPartitioned: boolean;
  isObservable: boolean;
  isMaterializable: boolean;
  isAutoCreatedStub: boolean;
  kinds: Array<string>;
  owners: Array<
    {__typename: 'TeamAssetOwner'; team: string} | {__typename: 'UserAssetOwner'; email: string}
  >;
  assetKey: {__typename: 'AssetKey'; path: Array<string>};
  tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
};

export type AssetNodeKeyFragment = {__typename: 'AssetKey'; path: Array<string>};
