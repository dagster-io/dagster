

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: TypeExplorerContainerQuery
// ====================================================

export interface TypeExplorerContainerQuery_type_RegularType_typeAttributes {
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

export interface TypeExplorerContainerQuery_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
  typeAttributes: TypeExplorerContainerQuery_type_RegularType_typeAttributes;
}

export interface TypeExplorerContainerQuery_type_CompositeType_typeAttributes {
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

export interface TypeExplorerContainerQuery_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface TypeExplorerContainerQuery_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: TypeExplorerContainerQuery_type_CompositeType_fields_type;
}

export interface TypeExplorerContainerQuery_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  typeAttributes: TypeExplorerContainerQuery_type_CompositeType_typeAttributes;
  fields: TypeExplorerContainerQuery_type_CompositeType_fields[];
}

export type TypeExplorerContainerQuery_type = TypeExplorerContainerQuery_type_RegularType | TypeExplorerContainerQuery_type_CompositeType;

export interface TypeExplorerContainerQuery {
  type: TypeExplorerContainerQuery_type | null;
}

export interface TypeExplorerContainerQueryVariables {
  pipelineName: string;
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