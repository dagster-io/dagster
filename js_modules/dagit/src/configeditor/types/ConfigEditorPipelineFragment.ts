/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigEditorPipelineFragment
// ====================================================

export interface ConfigEditorPipelineFragment_environmentType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorPipelineFragment_configTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType {
  __typename: "ListConfigType";
  key: string;
  name: string | null;
  isList: boolean;
  isNullable: boolean;
  ofType: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_ofType;
}

export type ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType = ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_EnumConfigType | ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType;

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  isOptional: boolean;
  configType: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType;
}

export interface ConfigEditorPipelineFragment_configTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  isSelector: boolean;
  fields: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields[];
}

export type ConfigEditorPipelineFragment_configTypes = ConfigEditorPipelineFragment_configTypes_EnumConfigType | ConfigEditorPipelineFragment_configTypes_CompositeConfigType;

export interface ConfigEditorPipelineFragment {
  __typename: "Pipeline";
  name: string;
  environmentType: ConfigEditorPipelineFragment_environmentType;
  configTypes: ConfigEditorPipelineFragment_configTypes[];
}
