/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: LaunchpadSessionPartitionSetsFragment
// ====================================================

export interface LaunchpadSessionPartitionSetsFragment_results {
  __typename: "PartitionSet";
  id: string;
  name: string;
  mode: string;
  solidSelection: string[] | null;
}

export interface LaunchpadSessionPartitionSetsFragment {
  __typename: "PartitionSets";
  results: LaunchpadSessionPartitionSetsFragment_results[];
}
