

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: TypeExplorerContainerQuery
// ====================================================

export interface TypeExplorerContainerQuery_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
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