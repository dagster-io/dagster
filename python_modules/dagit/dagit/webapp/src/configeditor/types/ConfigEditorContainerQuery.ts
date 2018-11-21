

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ConfigEditorContainerQuery
// ====================================================

export interface ConfigEditorContainerQuery_types_RegularType {
  __typename: "RegularType";
  name: string;
}

export interface ConfigEditorContainerQuery_types_CompositeType_fields_type {
  name: string;
}

export interface ConfigEditorContainerQuery_types_CompositeType_fields {
  name: string;
  type: ConfigEditorContainerQuery_types_CompositeType_fields_type;
}

export interface ConfigEditorContainerQuery_types_CompositeType {
  __typename: "CompositeType";
  name: string;
  fields: ConfigEditorContainerQuery_types_CompositeType_fields[];
}

export type ConfigEditorContainerQuery_types = ConfigEditorContainerQuery_types_RegularType | ConfigEditorContainerQuery_types_CompositeType;

export interface ConfigEditorContainerQuery {
  types: ConfigEditorContainerQuery_types[];
}

export interface ConfigEditorContainerQueryVariables {
  pipelineName: string;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

//==============================================================
// END Enums and Input Objects
//==============================================================