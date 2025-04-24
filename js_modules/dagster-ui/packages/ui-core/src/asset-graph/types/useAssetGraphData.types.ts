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
    isAutoCreatedStub: boolean;
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
    automationCondition: {
      __typename: 'AutomationCondition';
      label: string | null;
      expandedLabel: Array<string>;
    } | null;
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
  isAutoCreatedStub: boolean;
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
  automationCondition: {
    __typename: 'AutomationCondition';
    label: string | null;
    expandedLabel: Array<string>;
  } | null;
};

export const AssetGraphQueryVersion = '2320df17a1f6db4c51c59f89335c6830eebd2c4b14fa184edc4fcf28d3f6b132';
