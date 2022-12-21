/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PythonErrorFragment
// ====================================================

export interface PythonErrorFragment_errorChain_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PythonErrorFragment_errorChain {
  __typename: "ErrorChainLink";
  isExplicitLink: boolean;
  error: PythonErrorFragment_errorChain_error;
}

export interface PythonErrorFragment {
  __typename: "PythonError";
  message: string;
  stack: string[];
  errorChain: PythonErrorFragment_errorChain[];
}
