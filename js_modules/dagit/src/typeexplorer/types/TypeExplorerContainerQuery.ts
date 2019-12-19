// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: TypeExplorerContainerQuery
// ====================================================

export interface TypeExplorerContainerQuery_runtimeTypeOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "RuntimeTypeNotFoundError" | "PythonError";
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType" | "ListConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export type TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType;

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType {
  __typename: "EnumConfigType" | "ListConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType" | "ListConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export type TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType;

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export type TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType = TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_EnumConfigType | TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType_CompositeConfigType;

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType" | "ListConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export type TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType;

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType {
  __typename: "EnumConfigType" | "ListConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType" | "ListConfigType" | "NullableConfigType" | "RegularConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export type TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType;

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export type TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType = TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_EnumConfigType | TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType_CompositeConfigType;

export interface TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType {
  __typename: "RegularRuntimeType";
  name: string | null;
  description: string | null;
  inputSchemaType: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_inputSchemaType | null;
  outputSchemaType: TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType_outputSchemaType | null;
}

export type TypeExplorerContainerQuery_runtimeTypeOrError = TypeExplorerContainerQuery_runtimeTypeOrError_PipelineNotFoundError | TypeExplorerContainerQuery_runtimeTypeOrError_RegularRuntimeType;

export interface TypeExplorerContainerQuery {
  runtimeTypeOrError: TypeExplorerContainerQuery_runtimeTypeOrError;
}

export interface TypeExplorerContainerQueryVariables {
  pipelineName: string;
  runtimeTypeName: string;
}
