// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetGraphQueryVariables = Types.Exact<{
  pipelineSelector?: Types.InputMaybe<Types.PipelineSelector>;
  groupSelector?: Types.InputMaybe<Types.AssetGroupSelector>;
}>;

export type AssetGraphQuery = {
  __typename: 'Query';
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    groupName: string;
    isExecutable: boolean;
    changedReasons: Array<Types.ChangeReason>;
    hasMaterializePermission: boolean;
    graphName: string | null;
    jobNames: Array<string>;
    opNames: Array<string>;
    opVersion: string | null;
    description: string | null;
    computeKind: string | null;
    isPartitioned: boolean;
    isObservable: boolean;
    isMaterializable: boolean;
    kinds: Array<string>;
    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
    owners: Array<
      {__typename: 'TeamAssetOwner'; team: string} | {__typename: 'UserAssetOwner'; email: string}
    >;
    repository: {
      __typename: 'Repository';
      id: string;
      name: string;
      location: {__typename: 'RepositoryLocation'; id: string; name: string};
    };
    dependencyKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
    dependedByKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
  }>;
};

export type AssetNodeForGraphQueryFragment = {
  __typename: 'AssetNode';
  id: string;
  groupName: string;
  isExecutable: boolean;
  changedReasons: Array<Types.ChangeReason>;
  hasMaterializePermission: boolean;
  graphName: string | null;
  jobNames: Array<string>;
  opNames: Array<string>;
  opVersion: string | null;
  description: string | null;
  computeKind: string | null;
  isPartitioned: boolean;
  isObservable: boolean;
  isMaterializable: boolean;
  kinds: Array<string>;
  tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
  owners: Array<
    {__typename: 'TeamAssetOwner'; team: string} | {__typename: 'UserAssetOwner'; email: string}
  >;
  repository: {
    __typename: 'Repository';
    id: string;
    name: string;
    location: {__typename: 'RepositoryLocation'; id: string; name: string};
  };
  dependencyKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
  dependedByKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
  assetKey: {__typename: 'AssetKey'; path: Array<string>};
};
