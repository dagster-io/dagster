// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: TypeExplorerFragment
// ====================================================

export interface TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "EnumConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export type TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes = TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType;

export interface TypeExplorerFragment_inputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "EnumConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: TypeExplorerFragment_inputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "EnumConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export type TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes = TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType;

export interface TypeExplorerFragment_inputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_inputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: TypeExplorerFragment_inputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export type TypeExplorerFragment_inputSchemaType = TypeExplorerFragment_inputSchemaType_ArrayConfigType | TypeExplorerFragment_inputSchemaType_CompositeConfigType;

export interface TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "EnumConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export type TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes = TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType;

export interface TypeExplorerFragment_outputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "EnumConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: TypeExplorerFragment_outputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "EnumConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export type TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes = TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType;

export interface TypeExplorerFragment_outputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerFragment_outputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: TypeExplorerFragment_outputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export type TypeExplorerFragment_outputSchemaType = TypeExplorerFragment_outputSchemaType_ArrayConfigType | TypeExplorerFragment_outputSchemaType_CompositeConfigType;

export interface TypeExplorerFragment {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
  description: string | null;
  inputSchemaType: TypeExplorerFragment_inputSchemaType | null;
  outputSchemaType: TypeExplorerFragment_outputSchemaType | null;
}
