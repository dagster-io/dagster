// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigEditorGeneratorPartitionSetsFragment
// ====================================================

export interface ConfigEditorGeneratorPartitionSetsFragment_results {
  __typename: "PartitionSet";
  name: string;
  mode: string;
  solidSelection: string[] | null;
}

export interface ConfigEditorGeneratorPartitionSetsFragment {
  __typename: "PartitionSets";
  results: ConfigEditorGeneratorPartitionSetsFragment_results[];
}
