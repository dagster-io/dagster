// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ProcessStatusQuery
// ====================================================

export interface ProcessStatusQuery_instance {
  __typename: "Instance";
  info: string;
}

export interface ProcessStatusQuery {
  version: string;
  reloadSupported: boolean;
  instance: ProcessStatusQuery_instance;
}
