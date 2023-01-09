// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type SidebarOpDefinitionFragment_CompositeSolidDefinition_ = {
  __typename: 'CompositeSolidDefinition';
  id: string;
  name: string;
  description: string | null;
  inputMappings: Array<{
    __typename: 'InputMapping';
    definition: {__typename: 'InputDefinition'; name: string};
    mappedInput: {
      __typename: 'Input';
      definition: {__typename: 'InputDefinition'; name: string};
      solid: {__typename: 'Solid'; name: string};
    };
  }>;
  outputMappings: Array<{
    __typename: 'OutputMapping';
    definition: {__typename: 'OutputDefinition'; name: string};
    mappedOutput: {
      __typename: 'Output';
      definition: {__typename: 'OutputDefinition'; name: string};
      solid: {__typename: 'Solid'; name: string};
    };
  }>;
  metadata: Array<{__typename: 'MetadataItemDefinition'; key: string; value: string}>;
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
  }>;
  outputDefinitions: Array<{
    __typename: 'OutputDefinition';
    name: string;
    description: string | null;
    isDynamic: boolean | null;
    type:
      | {
          __typename: 'ListDagsterType';
          name: string | null;
          displayName: string;
          description: string | null;
        }
      | {
          __typename: 'NullableDagsterType';
          name: string | null;
          displayName: string;
          description: string | null;
        }
      | {
          __typename: 'RegularDagsterType';
          name: string | null;
          displayName: string;
          description: string | null;
        };
  }>;
  inputDefinitions: Array<{
    __typename: 'InputDefinition';
    name: string;
    description: string | null;
    type:
      | {
          __typename: 'ListDagsterType';
          name: string | null;
          displayName: string;
          description: string | null;
        }
      | {
          __typename: 'NullableDagsterType';
          name: string | null;
          displayName: string;
          description: string | null;
        }
      | {
          __typename: 'RegularDagsterType';
          name: string | null;
          displayName: string;
          description: string | null;
        };
  }>;
};

export type SidebarOpDefinitionFragment_SolidDefinition_ = {
  __typename: 'SolidDefinition';
  name: string;
  description: string | null;
  requiredResources: Array<{__typename: 'ResourceRequirement'; resourceKey: string}>;
  configField: {
    __typename: 'ConfigTypeField';
    configType:
      | {
          __typename: 'ArrayConfigType';
          key: string;
          description: string | null;
          isSelector: boolean;
          typeParamKeys: Array<string>;
          recursiveConfigTypes: Array<
            | {
                __typename: 'ArrayConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
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
              }
            | {
                __typename: 'EnumConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
                values: Array<{
                  __typename: 'EnumConfigValue';
                  value: string;
                  description: string | null;
                }>;
              }
            | {
                __typename: 'MapConfigType';
                keyLabelName: string | null;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'NullableConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'RegularConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'ScalarUnionConfigType';
                scalarTypeKey: string;
                nonScalarTypeKey: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
          >;
        }
      | {
          __typename: 'CompositeConfigType';
          key: string;
          description: string | null;
          isSelector: boolean;
          typeParamKeys: Array<string>;
          recursiveConfigTypes: Array<
            | {
                __typename: 'ArrayConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
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
              }
            | {
                __typename: 'EnumConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
                values: Array<{
                  __typename: 'EnumConfigValue';
                  value: string;
                  description: string | null;
                }>;
              }
            | {
                __typename: 'MapConfigType';
                keyLabelName: string | null;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'NullableConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'RegularConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'ScalarUnionConfigType';
                scalarTypeKey: string;
                nonScalarTypeKey: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
          >;
          fields: Array<{
            __typename: 'ConfigTypeField';
            name: string;
            description: string | null;
            isRequired: boolean;
            configTypeKey: string;
            defaultValueAsJson: string | null;
          }>;
        }
      | {
          __typename: 'EnumConfigType';
          givenName: string;
          key: string;
          description: string | null;
          isSelector: boolean;
          typeParamKeys: Array<string>;
          recursiveConfigTypes: Array<
            | {
                __typename: 'ArrayConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
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
              }
            | {
                __typename: 'EnumConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
                values: Array<{
                  __typename: 'EnumConfigValue';
                  value: string;
                  description: string | null;
                }>;
              }
            | {
                __typename: 'MapConfigType';
                keyLabelName: string | null;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'NullableConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'RegularConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'ScalarUnionConfigType';
                scalarTypeKey: string;
                nonScalarTypeKey: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
          >;
          values: Array<{__typename: 'EnumConfigValue'; value: string; description: string | null}>;
        }
      | {
          __typename: 'MapConfigType';
          keyLabelName: string | null;
          key: string;
          description: string | null;
          isSelector: boolean;
          typeParamKeys: Array<string>;
          recursiveConfigTypes: Array<
            | {
                __typename: 'ArrayConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
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
              }
            | {
                __typename: 'EnumConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
                values: Array<{
                  __typename: 'EnumConfigValue';
                  value: string;
                  description: string | null;
                }>;
              }
            | {
                __typename: 'MapConfigType';
                keyLabelName: string | null;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'NullableConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'RegularConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'ScalarUnionConfigType';
                scalarTypeKey: string;
                nonScalarTypeKey: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
          >;
        }
      | {
          __typename: 'NullableConfigType';
          key: string;
          description: string | null;
          isSelector: boolean;
          typeParamKeys: Array<string>;
          recursiveConfigTypes: Array<
            | {
                __typename: 'ArrayConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
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
              }
            | {
                __typename: 'EnumConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
                values: Array<{
                  __typename: 'EnumConfigValue';
                  value: string;
                  description: string | null;
                }>;
              }
            | {
                __typename: 'MapConfigType';
                keyLabelName: string | null;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'NullableConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'RegularConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'ScalarUnionConfigType';
                scalarTypeKey: string;
                nonScalarTypeKey: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
          >;
        }
      | {
          __typename: 'RegularConfigType';
          givenName: string;
          key: string;
          description: string | null;
          isSelector: boolean;
          typeParamKeys: Array<string>;
          recursiveConfigTypes: Array<
            | {
                __typename: 'ArrayConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
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
              }
            | {
                __typename: 'EnumConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
                values: Array<{
                  __typename: 'EnumConfigValue';
                  value: string;
                  description: string | null;
                }>;
              }
            | {
                __typename: 'MapConfigType';
                keyLabelName: string | null;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'NullableConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'RegularConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'ScalarUnionConfigType';
                scalarTypeKey: string;
                nonScalarTypeKey: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
          >;
        }
      | {
          __typename: 'ScalarUnionConfigType';
          scalarTypeKey: string;
          nonScalarTypeKey: string;
          key: string;
          description: string | null;
          isSelector: boolean;
          typeParamKeys: Array<string>;
          recursiveConfigTypes: Array<
            | {
                __typename: 'ArrayConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
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
              }
            | {
                __typename: 'EnumConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
                values: Array<{
                  __typename: 'EnumConfigValue';
                  value: string;
                  description: string | null;
                }>;
              }
            | {
                __typename: 'MapConfigType';
                keyLabelName: string | null;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'NullableConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'RegularConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'ScalarUnionConfigType';
                scalarTypeKey: string;
                nonScalarTypeKey: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
          >;
        };
  } | null;
  metadata: Array<{__typename: 'MetadataItemDefinition'; key: string; value: string}>;
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
  }>;
  outputDefinitions: Array<{
    __typename: 'OutputDefinition';
    name: string;
    description: string | null;
    isDynamic: boolean | null;
    type:
      | {
          __typename: 'ListDagsterType';
          name: string | null;
          displayName: string;
          description: string | null;
        }
      | {
          __typename: 'NullableDagsterType';
          name: string | null;
          displayName: string;
          description: string | null;
        }
      | {
          __typename: 'RegularDagsterType';
          name: string | null;
          displayName: string;
          description: string | null;
        };
  }>;
  inputDefinitions: Array<{
    __typename: 'InputDefinition';
    name: string;
    description: string | null;
    type:
      | {
          __typename: 'ListDagsterType';
          name: string | null;
          displayName: string;
          description: string | null;
        }
      | {
          __typename: 'NullableDagsterType';
          name: string | null;
          displayName: string;
          description: string | null;
        }
      | {
          __typename: 'RegularDagsterType';
          name: string | null;
          displayName: string;
          description: string | null;
        };
  }>;
};

export type SidebarOpDefinitionFragment =
  | SidebarOpDefinitionFragment_CompositeSolidDefinition_
  | SidebarOpDefinitionFragment_SolidDefinition_;
