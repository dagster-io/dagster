/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: TableSchemaFragment
// ====================================================

export interface TableSchemaFragment_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface TableSchemaFragment_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: TableSchemaFragment_columns_constraints;
}

export interface TableSchemaFragment_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface TableSchemaFragment {
  __typename: "TableSchema";
  columns: TableSchemaFragment_columns[];
  constraints: TableSchemaFragment_constraints | null;
}
