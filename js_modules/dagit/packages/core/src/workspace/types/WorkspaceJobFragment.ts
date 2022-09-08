/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: WorkspaceJobFragment
// ====================================================

export interface WorkspaceJobFragment_modes {
  __typename: "Mode";
  id: string;
  name: string;
}

export interface WorkspaceJobFragment {
  __typename: "Pipeline";
  id: string;
  name: string;
  isJob: boolean;
  modes: WorkspaceJobFragment_modes[];
}
