// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: TypeExplorerContainerQuery
// ====================================================

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "RuntimeTypeNotFoundError" | "PythonError";
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ArrayConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_RegularConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export type TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType = TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ArrayConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_RegularConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType_ScalarUnionConfigType;

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ArrayConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_RegularConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export type TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType = TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ArrayConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_RegularConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType_ScalarUnionConfigType;

export interface TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType {
  __typename: "RegularRuntimeType";
  name: string | null;
  description: string | null;
  inputSchemaType: TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_inputSchemaType | null;
  outputSchemaType: TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType_outputSchemaType | null;
}

export type TypeExplorerContainerQuery_pipeline_dagsterTypeOrError = TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_PipelineNotFoundError | TypeExplorerContainerQuery_pipeline_dagsterTypeOrError_RegularRuntimeType;

export interface TypeExplorerContainerQuery_pipeline {
  __typename: "Pipeline";
  dagsterTypeOrError: TypeExplorerContainerQuery_pipeline_dagsterTypeOrError;
}

export interface TypeExplorerContainerQuery {
  pipeline: TypeExplorerContainerQuery_pipeline;
}

export interface TypeExplorerContainerQueryVariables {
  pipelineName: string;
  dagsterTypeName: string;
}
