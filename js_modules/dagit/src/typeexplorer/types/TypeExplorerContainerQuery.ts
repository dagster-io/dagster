// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: TypeExplorerContainerQuery
// ====================================================

export interface TypeExplorerContainerQuery_pipelineOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "InvalidSubsetError" | "PythonError";
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "DagsterTypeNotFoundError" | "PythonError";
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ArrayConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_EnumConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_RegularConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_CompositeConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType_ScalarUnionConfigType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_fields[];
  recursiveConfigTypes: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType_recursiveConfigTypes[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ArrayConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_EnumConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_RegularConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_CompositeConfigType | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType_ScalarUnionConfigType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType {
  __typename: "RegularDagsterType";
  name: string | null;
  description: string | null;
  inputSchemaType: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_inputSchemaType | null;
  outputSchemaType: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType_outputSchemaType | null;
}

export type TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError = TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_PipelineNotFoundError | TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError_RegularDagsterType;

export interface TypeExplorerContainerQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  id: string;
  dagsterTypeOrError: TypeExplorerContainerQuery_pipelineOrError_Pipeline_dagsterTypeOrError;
}

export type TypeExplorerContainerQuery_pipelineOrError = TypeExplorerContainerQuery_pipelineOrError_PipelineNotFoundError | TypeExplorerContainerQuery_pipelineOrError_Pipeline;

export interface TypeExplorerContainerQuery {
  pipelineOrError: TypeExplorerContainerQuery_pipelineOrError;
}

export interface TypeExplorerContainerQueryVariables {
  pipelineSelector: PipelineSelector;
  dagsterTypeName: string;
}
