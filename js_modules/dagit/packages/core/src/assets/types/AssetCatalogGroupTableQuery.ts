/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetGroupSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetCatalogGroupTableQuery
// ====================================================

export interface AssetCatalogGroupTableQuery_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetCatalogGroupTableQuery_assetNodes_repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetCatalogGroupTableQuery_assetNodes_repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetCatalogGroupTableQuery_assetNodes_repository_location;
}

export interface AssetCatalogGroupTableQuery_assetNodes {
  __typename: "AssetNode";
  id: string;
  assetKey: AssetCatalogGroupTableQuery_assetNodes_assetKey;
  groupName: string | null;
  partitionDefinition: string | null;
  description: string | null;
  repository: AssetCatalogGroupTableQuery_assetNodes_repository;
}

export interface AssetCatalogGroupTableQuery {
  assetNodes: AssetCatalogGroupTableQuery_assetNodes[];
}

export interface AssetCatalogGroupTableQueryVariables {
  group?: AssetGroupSelector | null;
}
