/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: TypeExplorerFragment
// ====================================================

export interface TypeExplorerFragment_inputSchemaType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface TypeExplorerFragment_inputSchemaType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: TypeExplorerFragment_inputSchemaType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface TypeExplorerFragment_inputSchemaType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface TypeExplorerFragment_inputSchemaType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface TypeExplorerFragment_inputSchemaType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: TypeExplorerFragment_inputSchemaType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface TypeExplorerFragment_inputSchemaType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: TypeExplorerFragment_inputSchemaType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: TypeExplorerFragment_inputSchemaType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type TypeExplorerFragment_inputSchemaType_EnumConfigType_innerTypes = TypeExplorerFragment_inputSchemaType_EnumConfigType_innerTypes_EnumConfigType | TypeExplorerFragment_inputSchemaType_EnumConfigType_innerTypes_CompositeConfigType;

export interface TypeExplorerFragment_inputSchemaType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: TypeExplorerFragment_inputSchemaType_EnumConfigType_innerTypes[];
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: TypeExplorerFragment_inputSchemaType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: TypeExplorerFragment_inputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: TypeExplorerFragment_inputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: TypeExplorerFragment_inputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type TypeExplorerFragment_inputSchemaType_CompositeConfigType_innerTypes = TypeExplorerFragment_inputSchemaType_CompositeConfigType_innerTypes_EnumConfigType | TypeExplorerFragment_inputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: TypeExplorerFragment_inputSchemaType_CompositeConfigType_fields_configType;
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: TypeExplorerFragment_inputSchemaType_CompositeConfigType_innerTypes[];
  fields: TypeExplorerFragment_inputSchemaType_CompositeConfigType_fields[];
}

export type TypeExplorerFragment_inputSchemaType = TypeExplorerFragment_inputSchemaType_EnumConfigType | TypeExplorerFragment_inputSchemaType_CompositeConfigType;

export interface TypeExplorerFragment_outputSchemaType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface TypeExplorerFragment_outputSchemaType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: TypeExplorerFragment_outputSchemaType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface TypeExplorerFragment_outputSchemaType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface TypeExplorerFragment_outputSchemaType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface TypeExplorerFragment_outputSchemaType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: TypeExplorerFragment_outputSchemaType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface TypeExplorerFragment_outputSchemaType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: TypeExplorerFragment_outputSchemaType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: TypeExplorerFragment_outputSchemaType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type TypeExplorerFragment_outputSchemaType_EnumConfigType_innerTypes = TypeExplorerFragment_outputSchemaType_EnumConfigType_innerTypes_EnumConfigType | TypeExplorerFragment_outputSchemaType_EnumConfigType_innerTypes_CompositeConfigType;

export interface TypeExplorerFragment_outputSchemaType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: TypeExplorerFragment_outputSchemaType_EnumConfigType_innerTypes[];
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: TypeExplorerFragment_outputSchemaType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: TypeExplorerFragment_outputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: TypeExplorerFragment_outputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: TypeExplorerFragment_outputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type TypeExplorerFragment_outputSchemaType_CompositeConfigType_innerTypes = TypeExplorerFragment_outputSchemaType_CompositeConfigType_innerTypes_EnumConfigType | TypeExplorerFragment_outputSchemaType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: TypeExplorerFragment_outputSchemaType_CompositeConfigType_fields_configType;
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: TypeExplorerFragment_outputSchemaType_CompositeConfigType_innerTypes[];
  fields: TypeExplorerFragment_outputSchemaType_CompositeConfigType_fields[];
}

export type TypeExplorerFragment_outputSchemaType = TypeExplorerFragment_outputSchemaType_EnumConfigType | TypeExplorerFragment_outputSchemaType_CompositeConfigType;

export interface TypeExplorerFragment {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
  description: string | null;
  inputSchemaType: TypeExplorerFragment_inputSchemaType | null;
  outputSchemaType: TypeExplorerFragment_outputSchemaType | null;
}
