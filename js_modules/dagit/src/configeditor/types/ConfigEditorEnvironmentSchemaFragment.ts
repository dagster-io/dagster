// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigEditorEnvironmentSchemaFragment
// ====================================================

export interface ConfigEditorEnvironmentSchemaFragment_rootEnvironmentType {
  __typename: "ArrayConfigType" | "CompositeConfigType" | "EnumConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  values: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType_values[];
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType_fields[];
}

export type ConfigEditorEnvironmentSchemaFragment_allConfigTypes = ConfigEditorEnvironmentSchemaFragment_allConfigTypes_ArrayConfigType | ConfigEditorEnvironmentSchemaFragment_allConfigTypes_EnumConfigType | ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType;

export interface ConfigEditorEnvironmentSchemaFragment {
  __typename: "EnvironmentSchema";
  rootEnvironmentType: ConfigEditorEnvironmentSchemaFragment_rootEnvironmentType;
  allConfigTypes: ConfigEditorEnvironmentSchemaFragment_allConfigTypes[];
}
