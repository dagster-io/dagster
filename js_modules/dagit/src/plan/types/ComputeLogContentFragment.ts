// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ComputeLogContentFragment
// ====================================================

export interface ComputeLogContentFragment_stdout {
  __typename: "ComputeLogFile";
  path: string;
  data: string;
  downloadUrl: string;
}

export interface ComputeLogContentFragment_stderr {
  __typename: "ComputeLogFile";
  path: string;
  data: string;
  downloadUrl: string;
}

export interface ComputeLogContentFragment {
  __typename: "ComputeLogs";
  stdout: ComputeLogContentFragment_stdout | null;
  stderr: ComputeLogContentFragment_stderr | null;
}
