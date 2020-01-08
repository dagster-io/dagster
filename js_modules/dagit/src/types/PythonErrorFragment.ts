// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PythonErrorFragment
// ====================================================

export interface PythonErrorFragment_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PythonErrorFragment {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PythonErrorFragment_cause | null;
}
