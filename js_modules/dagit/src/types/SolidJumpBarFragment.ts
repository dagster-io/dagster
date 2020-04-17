// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SolidJumpBarFragment
// ====================================================

export interface SolidJumpBarFragment_solids {
  __typename: "Solid";
  name: string;
}

export interface SolidJumpBarFragment {
  __typename: "Pipeline" | "PipelineSnapshot";
  solids: SolidJumpBarFragment_solids[];
}
