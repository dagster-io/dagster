// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ExecutionSessionContainerPartitionSetsFragment
// ====================================================

export interface ExecutionSessionContainerPartitionSetsFragment_results {
  __typename: "PartitionSet";
  name: string;
  mode: string;
  solidSelection: string[] | null;
}

export interface ExecutionSessionContainerPartitionSetsFragment {
  __typename: "PartitionSets";
  results: ExecutionSessionContainerPartitionSetsFragment_results[];
}
