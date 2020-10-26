// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigEditorHelpConfigTypeFragment
// ====================================================

export interface ConfigEditorHelpConfigTypeFragment_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface ConfigEditorHelpConfigTypeFragment_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface ConfigEditorHelpConfigTypeFragment_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface ConfigEditorHelpConfigTypeFragment_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface ConfigEditorHelpConfigTypeFragment_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: ConfigEditorHelpConfigTypeFragment_CompositeConfigType_fields[];
}

export interface ConfigEditorHelpConfigTypeFragment_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type ConfigEditorHelpConfigTypeFragment = ConfigEditorHelpConfigTypeFragment_ArrayConfigType | ConfigEditorHelpConfigTypeFragment_EnumConfigType | ConfigEditorHelpConfigTypeFragment_RegularConfigType | ConfigEditorHelpConfigTypeFragment_CompositeConfigType | ConfigEditorHelpConfigTypeFragment_ScalarUnionConfigType;
