// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigEditorHelpConfigTypeFragment
// ====================================================

export interface ConfigEditorHelpConfigTypeFragment_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorHelpConfigTypeFragment_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorHelpConfigTypeFragment_EnumConfigType_innerTypes[];
}

export interface ConfigEditorHelpConfigTypeFragment_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorHelpConfigTypeFragment_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface ConfigEditorHelpConfigTypeFragment_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: ConfigEditorHelpConfigTypeFragment_CompositeConfigType_fields_configType;
}

export interface ConfigEditorHelpConfigTypeFragment_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: ConfigEditorHelpConfigTypeFragment_CompositeConfigType_innerTypes[];
  fields: ConfigEditorHelpConfigTypeFragment_CompositeConfigType_fields[];
}

export type ConfigEditorHelpConfigTypeFragment = ConfigEditorHelpConfigTypeFragment_EnumConfigType | ConfigEditorHelpConfigTypeFragment_CompositeConfigType;
