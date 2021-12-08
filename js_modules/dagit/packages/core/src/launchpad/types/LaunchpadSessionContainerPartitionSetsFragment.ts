/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: LaunchpadSessionContainerPartitionSetsFragment
// ====================================================

export interface LaunchpadSessionContainerPartitionSetsFragment_results {
  __typename: "PartitionSet";
  id: string;
  name: string;
  mode: string;
  solidSelection: string[] | null;
}

export interface LaunchpadSessionContainerPartitionSetsFragment {
  __typename: "PartitionSets";
  results: LaunchpadSessionContainerPartitionSetsFragment_results[];
}
