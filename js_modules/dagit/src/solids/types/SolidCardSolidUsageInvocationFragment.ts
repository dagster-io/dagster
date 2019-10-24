// @generated
// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SolidCardSolidUsageInvocationFragment
// ====================================================

export interface SolidCardSolidUsageInvocationFragment_pipeline {
  __typename: "Pipeline";
  name: string;
}

export interface SolidCardSolidUsageInvocationFragment_solidHandle {
  __typename: "SolidHandle";
  handleID: string;
}

export interface SolidCardSolidUsageInvocationFragment {
  __typename: "SolidUsageInvocation";
  pipeline: SolidCardSolidUsageInvocationFragment_pipeline;
  solidHandle: SolidCardSolidUsageInvocationFragment_solidHandle;
}
