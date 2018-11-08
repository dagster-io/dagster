

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: GetTypeDetails
// ====================================================

export interface GetTypeDetails_type_typeAttributes {
  /**
   * 
   * True if the system defines it and it is the same type across pipelines.
   * Examples include "Int" and "String."
   */
  isBuiltin: boolean;
  /**
   * 
   * Dagster generates types for base elements of the config system (e.g. the solids and
   * context field of the base environment). These types are always present
   * and are typically not relevant to an end user. This flag allows tool authors to
   * filter out those types by default.
   * 
   */
  isSystemConfig: boolean;
}

export interface GetTypeDetails_type {
  name: string;
  description: string | null;
  typeAttributes: GetTypeDetails_type_typeAttributes;
}

export interface GetTypeDetails {
  type: GetTypeDetails_type | null;
}

export interface GetTypeDetailsVariables {
  typeName: string;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

//==============================================================
// END Enums and Input Objects
//==============================================================