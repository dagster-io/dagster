

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: TypeExplorerFragment
// ====================================================

export interface TypeExplorerFragment_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface TypeExplorerFragment_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface TypeExplorerFragment_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  type: TypeExplorerFragment_CompositeType_fields_type;
}

export interface TypeExplorerFragment_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: TypeExplorerFragment_CompositeType_fields[];
}

export type TypeExplorerFragment = TypeExplorerFragment_RegularType | TypeExplorerFragment_CompositeType;

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

//==============================================================
// END Enums and Input Objects
//==============================================================