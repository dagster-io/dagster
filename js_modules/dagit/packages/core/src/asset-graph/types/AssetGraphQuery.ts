/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector, AssetGroupSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetGraphQuery
// ====================================================

export interface AssetGraphQuery_assetNodes_repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetGraphQuery_assetNodes_repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetGraphQuery_assetNodes_repository_location;
}

export interface AssetGraphQuery_assetNodes_dependencyKeys {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphQuery_assetNodes_dependedByKeys {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphQuery_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphQuery_assetNodes {
  __typename: "AssetNode";
  id: string;
  groupName: string | null;
  repository: AssetGraphQuery_assetNodes_repository;
  dependencyKeys: AssetGraphQuery_assetNodes_dependencyKeys[];
  dependedByKeys: AssetGraphQuery_assetNodes_dependedByKeys[];
  graphName: string | null;
  jobNames: string[];
  opNames: string[];
  opVersion: string | null;
  description: string | null;
  computeKind: string | null;
  isSource: boolean;
  assetKey: AssetGraphQuery_assetNodes_assetKey;
  isVersioned: boolean;
}

export interface AssetGraphQuery {
  assetNodes: AssetGraphQuery_assetNodes[];
}

export interface AssetGraphQueryVariables {
  pipelineSelector?: PipelineSelector | null;
  groupSelector?: AssetGroupSelector | null;
}
