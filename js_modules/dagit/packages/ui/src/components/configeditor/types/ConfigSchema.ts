/**
 * This is a manual copy of the config schema type generated for Dagit.
 */

export interface ConfigSchema_rootConfigType {
  __typename:
    | 'EnumConfigType'
    | 'CompositeConfigType'
    | 'RegularConfigType'
    | 'ArrayConfigType'
    | 'NullableConfigType'
    | 'ScalarUnionConfigType'
    | 'MapConfigType';
  key: string;
}

export interface ConfigSchema_allConfigTypes_ArrayConfigType {
  __typename: 'ArrayConfigType';
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

// Separated from `ArrayConfigType` manually to improve refinement.
export interface ConfigSchema_allConfigTypes_NullableConfigType {
  __typename: 'NullableConfigType';
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface ConfigSchema_allConfigTypes_RegularConfigType {
  __typename: 'RegularConfigType';
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface ConfigSchema_allConfigTypes_MapConfigType {
  __typename: 'MapConfigType';
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  keyLabelName: string | null;
}

export interface ConfigSchema_allConfigTypes_EnumConfigType_values {
  __typename: 'EnumConfigValue';
  value: string;
  description: string | null;
}

export interface ConfigSchema_allConfigTypes_EnumConfigType {
  __typename: 'EnumConfigType';
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  values: ConfigSchema_allConfigTypes_EnumConfigType_values[];
}

export interface ConfigSchema_allConfigTypes_CompositeConfigType_fields {
  __typename: 'ConfigTypeField';
  name: string;
  description: string | null;
  isRequired: boolean;
  configTypeKey: string;
  defaultValueAsJson: string | null;
}

export interface ConfigSchema_allConfigTypes_CompositeConfigType {
  __typename: 'CompositeConfigType';
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: ConfigSchema_allConfigTypes_CompositeConfigType_fields[];
}

export interface ConfigSchema_allConfigTypes_ScalarUnionConfigType {
  __typename: 'ScalarUnionConfigType';
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type ConfigSchema_allConfigTypes =
  | ConfigSchema_allConfigTypes_ArrayConfigType
  | ConfigSchema_allConfigTypes_NullableConfigType
  | ConfigSchema_allConfigTypes_RegularConfigType
  | ConfigSchema_allConfigTypes_MapConfigType
  | ConfigSchema_allConfigTypes_EnumConfigType
  | ConfigSchema_allConfigTypes_CompositeConfigType
  | ConfigSchema_allConfigTypes_ScalarUnionConfigType;

export interface ConfigSchema {
  __typename: string;
  rootConfigType: ConfigSchema_rootConfigType;
  allConfigTypes: ConfigSchema_allConfigTypes[];
}
