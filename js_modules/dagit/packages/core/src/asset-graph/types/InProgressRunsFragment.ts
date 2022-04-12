/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: InProgressRunsFragment
// ====================================================

export interface InProgressRunsFragment_unstartedRuns {
  __typename: "Run";
  id: string;
}

export interface InProgressRunsFragment_inProgressRuns {
  __typename: "Run";
  id: string;
}

export interface InProgressRunsFragment {
  __typename: "InProgressRunsByStep";
  stepKey: string;
  unstartedRuns: InProgressRunsFragment_unstartedRuns[];
  inProgressRuns: InProgressRunsFragment_inProgressRuns[];
}
