// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ConfigTypeSchemaFragment_ArrayConfigType_ = {
  __typename: 'ArrayConfigType';
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: Array<string>;
};

export type ConfigTypeSchemaFragment_CompositeConfigType_ = {
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

export type ConfigTypeSchemaFragment_EnumConfigType_ = {
  __typename: 'EnumConfigType';
  givenName: string;
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: Array<string>;
  values: Array<{__typename: 'EnumConfigValue'; value: string; description: string | null}>;
};

export type ConfigTypeSchemaFragment_MapConfigType_ = {
  __typename: 'MapConfigType';
  keyLabelName: string | null;
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: Array<string>;
};

export type ConfigTypeSchemaFragment_NullableConfigType_ = {
  __typename: 'NullableConfigType';
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: Array<string>;
};

export type ConfigTypeSchemaFragment_RegularConfigType_ = {
  __typename: 'RegularConfigType';
  givenName: string;
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: Array<string>;
};

export type ConfigTypeSchemaFragment_ScalarUnionConfigType_ = {
  __typename: 'ScalarUnionConfigType';
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: Array<string>;
};

export type ConfigTypeSchemaFragment =
  | ConfigTypeSchemaFragment_ArrayConfigType_
  | ConfigTypeSchemaFragment_CompositeConfigType_
  | ConfigTypeSchemaFragment_EnumConfigType_
  | ConfigTypeSchemaFragment_MapConfigType_
  | ConfigTypeSchemaFragment_NullableConfigType_
  | ConfigTypeSchemaFragment_RegularConfigType_
  | ConfigTypeSchemaFragment_ScalarUnionConfigType_;
