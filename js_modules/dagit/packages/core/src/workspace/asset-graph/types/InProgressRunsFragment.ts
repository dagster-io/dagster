/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: InProgressRunsFragment
// ====================================================

export interface InProgressRunsFragment_runs {
  __typename: "Run";
  id: string;
  runId: string;
}

export interface InProgressRunsFragment {
  __typename: "InProgressRunsByStep";
  stepKey: string;
  runs: InProgressRunsFragment_runs[];
}
