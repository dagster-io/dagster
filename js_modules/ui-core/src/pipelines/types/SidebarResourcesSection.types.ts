// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type SidebarResourcesSectionFragment = {
  __typename: 'Mode';
  id: string;
  name: string;
  description: string | null;
  resources: Array<{
    __typename: 'Resource';
    name: string;
    description: string | null;
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
  }>;
  loggers: Array<{
    __typename: 'Logger';
    name: string;
    description: string | null;
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
  }>;
};
