// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ConfigTypeSchemaFragment_ArrayConfigType = {
  __typename: 'ArrayConfigType';
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: Array<string>;
};

export type ConfigTypeSchemaFragment_CompositeConfigType = {
  __typename: 'CompositeConfigType';
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: Array<string>;
  fields: Array<{
    __typename: 'ConfigTypeField';
    name: string;
    description: string | null;
    isRequired: boolean;
    configTypeKey: string;
    defaultValueAsJson: string | null;
  }>;
};

export type ConfigTypeSchemaFragment_EnumConfigType = {
  __typename: 'EnumConfigType';
  givenName: string;
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: Array<string>;
  values: Array<{__typename: 'EnumConfigValue'; value: string; description: string | null}>;
};

export type ConfigTypeSchemaFragment_MapConfigType = {
  __typename: 'MapConfigType';
  keyLabelName: string | null;
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: Array<string>;
};

export type ConfigTypeSchemaFragment_NullableConfigType = {
  __typename: 'NullableConfigType';
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: Array<string>;
};

export type ConfigTypeSchemaFragment_RegularConfigType = {
  __typename: 'RegularConfigType';
  givenName: string;
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: Array<string>;
};

export type ConfigTypeSchemaFragment_ScalarUnionConfigType = {
  __typename: 'ScalarUnionConfigType';
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: Array<string>;
};

export type ConfigTypeSchemaFragment =
  | ConfigTypeSchemaFragment_ArrayConfigType
  | ConfigTypeSchemaFragment_CompositeConfigType
  | ConfigTypeSchemaFragment_EnumConfigType
  | ConfigTypeSchemaFragment_MapConfigType
  | ConfigTypeSchemaFragment_NullableConfigType
  | ConfigTypeSchemaFragment_RegularConfigType
  | ConfigTypeSchemaFragment_ScalarUnionConfigType;
