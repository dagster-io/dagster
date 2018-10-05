

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigFragment
// ====================================================

export interface ConfigFragment_type_RegularType {
  __typename: "RegularType";
  name: string;
  description: string | null;
}

export interface ConfigFragment_type_CompositeType_fields_type_RegularType {
  name: string;
  description: string | null;
}

export interface ConfigFragment_type_CompositeType_fields_type_CompositeType_fields_type {
  name: string;
  description: string | null;
}

export interface ConfigFragment_type_CompositeType_fields_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: ConfigFragment_type_CompositeType_fields_type_CompositeType_fields_type;
}

export interface ConfigFragment_type_CompositeType_fields_type_CompositeType {
  name: string;
  description: string | null;
  fields: ConfigFragment_type_CompositeType_fields_type_CompositeType_fields[];
}

export type ConfigFragment_type_CompositeType_fields_type = ConfigFragment_type_CompositeType_fields_type_RegularType | ConfigFragment_type_CompositeType_fields_type_CompositeType;

export interface ConfigFragment_type_CompositeType_fields {
  name: string;
  description: string | null;
  isOptional: boolean;
  defaultValue: string | null;
  type: ConfigFragment_type_CompositeType_fields_type;
}

export interface ConfigFragment_type_CompositeType {
  __typename: "CompositeType";
  name: string;
  description: string | null;
  fields: ConfigFragment_type_CompositeType_fields[];
}

export type ConfigFragment_type = ConfigFragment_type_RegularType | ConfigFragment_type_CompositeType;

export interface ConfigFragment {
  type: ConfigFragment_type;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

//==============================================================
// END Enums and Input Objects
//==============================================================