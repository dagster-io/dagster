/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: InstanceConfigQuery
// ====================================================

export interface InstanceConfigQuery_instance {
  __typename: "Instance";
  info: string | null;
}

export interface InstanceConfigQuery {
  version: string;
  instance: InstanceConfigQuery_instance;
}
