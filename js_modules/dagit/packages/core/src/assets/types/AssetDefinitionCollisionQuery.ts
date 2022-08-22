/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetKeyInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetDefinitionCollisionQuery
// ====================================================

export interface AssetDefinitionCollisionQuery_assetNodeDefinitionCollisions_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetDefinitionCollisionQuery_assetNodeDefinitionCollisions_repositories_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetDefinitionCollisionQuery_assetNodeDefinitionCollisions_repositories {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetDefinitionCollisionQuery_assetNodeDefinitionCollisions_repositories_location;
}

export interface AssetDefinitionCollisionQuery_assetNodeDefinitionCollisions {
  __typename: "AssetNodeDefinitionCollision";
  assetKey: AssetDefinitionCollisionQuery_assetNodeDefinitionCollisions_assetKey;
  repositories: AssetDefinitionCollisionQuery_assetNodeDefinitionCollisions_repositories[];
}

export interface AssetDefinitionCollisionQuery {
  assetNodeDefinitionCollisions: AssetDefinitionCollisionQuery_assetNodeDefinitionCollisions[];
}

export interface AssetDefinitionCollisionQueryVariables {
  assetKeys: AssetKeyInput[];
}
