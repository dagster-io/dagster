// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigEditorRunConfigSchemaFragment
// ====================================================

export interface ConfigEditorRunConfigSchemaFragment_rootConfigType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ArrayConfigType" | "NullableConfigType" | "ScalarUnionConfigType";
  key: string;
}

export interface ConfigEditorRunConfigSchemaFragment_allConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface ConfigEditorRunConfigSchemaFragment_allConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface ConfigEditorRunConfigSchemaFragment_allConfigTypes_EnumConfigType_values {
  __typename: "EnumConfigValue";
  value: string;
  description: string | null;
}

export interface ConfigEditorRunConfigSchemaFragment_allConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: ConfigEditorRunConfigSchemaFragment_allConfigTypes_EnumConfigType_values[];
}

export interface ConfigEditorRunConfigSchemaFragment_allConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface ConfigEditorRunConfigSchemaFragment_allConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: ConfigEditorRunConfigSchemaFragment_allConfigTypes_CompositeConfigType_fields[];
}

export interface ConfigEditorRunConfigSchemaFragment_allConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type ConfigEditorRunConfigSchemaFragment_allConfigTypes = ConfigEditorRunConfigSchemaFragment_allConfigTypes_ArrayConfigType | ConfigEditorRunConfigSchemaFragment_allConfigTypes_RegularConfigType | ConfigEditorRunConfigSchemaFragment_allConfigTypes_EnumConfigType | ConfigEditorRunConfigSchemaFragment_allConfigTypes_CompositeConfigType | ConfigEditorRunConfigSchemaFragment_allConfigTypes_ScalarUnionConfigType;

export interface ConfigEditorRunConfigSchemaFragment {
  __typename: "RunConfigSchema";
  rootConfigType: ConfigEditorRunConfigSchemaFragment_rootConfigType;
  allConfigTypes: ConfigEditorRunConfigSchemaFragment_allConfigTypes[];
}
