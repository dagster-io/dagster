/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: PermissionsQuery
// ====================================================

export interface PermissionsQuery_permissions {
  __typename: "Permission";
  permission: string;
  value: boolean;
  disabledReason: string | null;
}

export interface PermissionsQuery {
  permissions: PermissionsQuery_permissions[];
}
