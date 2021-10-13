// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: AssetTableFragment
// ====================================================

export interface AssetTableFragment_key {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetTableFragment_definition {
  __typename: "AssetNode";
  id: string;
  opName: string | null;
  jobName: string | null;
  description: string | null;
}

export interface AssetTableFragment {
  __typename: "Asset";
  id: string;
  key: AssetTableFragment_key;
  definition: AssetTableFragment_definition | null;
}
