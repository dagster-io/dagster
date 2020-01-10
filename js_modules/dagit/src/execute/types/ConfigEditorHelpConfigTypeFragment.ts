// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigEditorHelpConfigTypeFragment
// ====================================================

export interface ConfigEditorHelpConfigTypeFragment_ArrayConfigType {
  __typename: "ArrayConfigType" | "EnumConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface ConfigEditorHelpConfigTypeFragment_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface ConfigEditorHelpConfigTypeFragment_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: ConfigEditorHelpConfigTypeFragment_CompositeConfigType_fields[];
}

export type ConfigEditorHelpConfigTypeFragment = ConfigEditorHelpConfigTypeFragment_ArrayConfigType | ConfigEditorHelpConfigTypeFragment_CompositeConfigType;
