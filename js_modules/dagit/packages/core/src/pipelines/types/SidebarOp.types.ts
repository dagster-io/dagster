// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type SidebarOpFragment_CompositeSolidDefinition_ = {
  __typename: 'CompositeSolidDefinition';
  id: string;
  name: string;
  solidHandle: {
    __typename: 'SolidHandle';
    solid: {
      __typename: 'Solid';
      name: string;
      definition:
        | {
            __typename: 'CompositeSolidDefinition';
            id: string;
            name: string;
            description: string | null;
            metadata: Array<{__typename: 'MetadataItemDefinition'; key: string; value: string}>;
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
          }
        | {
            __typename: 'SolidDefinition';
            name: string;
            description: string | null;
            metadata: Array<{__typename: 'MetadataItemDefinition'; key: string; value: string}>;
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
      inputs: Array<{
        __typename: 'Input';
        isDynamicCollect: boolean;
        definition: {
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
        };
        dependsOn: Array<{
          __typename: 'Output';
          definition: {__typename: 'OutputDefinition'; name: string};
          solid: {__typename: 'Solid'; name: string};
        }>;
      }>;
      outputs: Array<{
        __typename: 'Output';
        definition: {
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
        };
        dependedBy: Array<{
          __typename: 'Input';
          definition: {__typename: 'InputDefinition'; name: string};
          solid: {__typename: 'Solid'; name: string};
        }>;
      }>;
    };
  } | null;
};

export type SidebarOpFragment_Graph_ = {
  __typename: 'Graph';
  id: string;
  name: string;
  solidHandle: {
    __typename: 'SolidHandle';
    solid: {
      __typename: 'Solid';
      name: string;
      definition:
        | {
            __typename: 'CompositeSolidDefinition';
            id: string;
            name: string;
            description: string | null;
            metadata: Array<{__typename: 'MetadataItemDefinition'; key: string; value: string}>;
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
          }
        | {
            __typename: 'SolidDefinition';
            name: string;
            description: string | null;
            metadata: Array<{__typename: 'MetadataItemDefinition'; key: string; value: string}>;
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
      inputs: Array<{
        __typename: 'Input';
        isDynamicCollect: boolean;
        definition: {
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
        };
        dependsOn: Array<{
          __typename: 'Output';
          definition: {__typename: 'OutputDefinition'; name: string};
          solid: {__typename: 'Solid'; name: string};
        }>;
      }>;
      outputs: Array<{
        __typename: 'Output';
        definition: {
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
        };
        dependedBy: Array<{
          __typename: 'Input';
          definition: {__typename: 'InputDefinition'; name: string};
          solid: {__typename: 'Solid'; name: string};
        }>;
      }>;
    };
  } | null;
};

export type SidebarOpFragment_Job_ = {
  __typename: 'Job';
  id: string;
  name: string;
  solidHandle: {
    __typename: 'SolidHandle';
    solid: {
      __typename: 'Solid';
      name: string;
      definition:
        | {
            __typename: 'CompositeSolidDefinition';
            id: string;
            name: string;
            description: string | null;
            metadata: Array<{__typename: 'MetadataItemDefinition'; key: string; value: string}>;
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
          }
        | {
            __typename: 'SolidDefinition';
            name: string;
            description: string | null;
            metadata: Array<{__typename: 'MetadataItemDefinition'; key: string; value: string}>;
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
      inputs: Array<{
        __typename: 'Input';
        isDynamicCollect: boolean;
        definition: {
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
        };
        dependsOn: Array<{
          __typename: 'Output';
          definition: {__typename: 'OutputDefinition'; name: string};
          solid: {__typename: 'Solid'; name: string};
        }>;
      }>;
      outputs: Array<{
        __typename: 'Output';
        definition: {
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
        };
        dependedBy: Array<{
          __typename: 'Input';
          definition: {__typename: 'InputDefinition'; name: string};
          solid: {__typename: 'Solid'; name: string};
        }>;
      }>;
    };
  } | null;
};

export type SidebarOpFragment_Pipeline_ = {
  __typename: 'Pipeline';
  id: string;
  name: string;
  solidHandle: {
    __typename: 'SolidHandle';
    solid: {
      __typename: 'Solid';
      name: string;
      definition:
        | {
            __typename: 'CompositeSolidDefinition';
            id: string;
            name: string;
            description: string | null;
            metadata: Array<{__typename: 'MetadataItemDefinition'; key: string; value: string}>;
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
          }
        | {
            __typename: 'SolidDefinition';
            name: string;
            description: string | null;
            metadata: Array<{__typename: 'MetadataItemDefinition'; key: string; value: string}>;
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
      inputs: Array<{
        __typename: 'Input';
        isDynamicCollect: boolean;
        definition: {
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
        };
        dependsOn: Array<{
          __typename: 'Output';
          definition: {__typename: 'OutputDefinition'; name: string};
          solid: {__typename: 'Solid'; name: string};
        }>;
      }>;
      outputs: Array<{
        __typename: 'Output';
        definition: {
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
        };
        dependedBy: Array<{
          __typename: 'Input';
          definition: {__typename: 'InputDefinition'; name: string};
          solid: {__typename: 'Solid'; name: string};
        }>;
      }>;
    };
  } | null;
};

export type SidebarOpFragment_PipelineSnapshot_ = {
  __typename: 'PipelineSnapshot';
  id: string;
  name: string;
  solidHandle: {
    __typename: 'SolidHandle';
    solid: {
      __typename: 'Solid';
      name: string;
      definition:
        | {
            __typename: 'CompositeSolidDefinition';
            id: string;
            name: string;
            description: string | null;
            metadata: Array<{__typename: 'MetadataItemDefinition'; key: string; value: string}>;
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
          }
        | {
            __typename: 'SolidDefinition';
            name: string;
            description: string | null;
            metadata: Array<{__typename: 'MetadataItemDefinition'; key: string; value: string}>;
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
      inputs: Array<{
        __typename: 'Input';
        isDynamicCollect: boolean;
        definition: {
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
        };
        dependsOn: Array<{
          __typename: 'Output';
          definition: {__typename: 'OutputDefinition'; name: string};
          solid: {__typename: 'Solid'; name: string};
        }>;
      }>;
      outputs: Array<{
        __typename: 'Output';
        definition: {
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
        };
        dependedBy: Array<{
          __typename: 'Input';
          definition: {__typename: 'InputDefinition'; name: string};
          solid: {__typename: 'Solid'; name: string};
        }>;
      }>;
    };
  } | null;
};

export type SidebarOpFragment =
  | SidebarOpFragment_CompositeSolidDefinition_
  | SidebarOpFragment_Graph_
  | SidebarOpFragment_Job_
  | SidebarOpFragment_Pipeline_
  | SidebarOpFragment_PipelineSnapshot_;

export type SidebarPipelineOpQueryVariables = Types.Exact<{
  selector: Types.PipelineSelector;
  handleID: Types.Scalars['String'];
}>;

export type SidebarPipelineOpQuery = {
  __typename: 'DagitQuery';
  pipelineOrError:
    | {__typename: 'InvalidSubsetError'}
    | {
        __typename: 'Pipeline';
        id: string;
        name: string;
        solidHandle: {
          __typename: 'SolidHandle';
          solid: {
            __typename: 'Solid';
            name: string;
            definition:
              | {
                  __typename: 'CompositeSolidDefinition';
                  id: string;
                  name: string;
                  description: string | null;
                  metadata: Array<{
                    __typename: 'MetadataItemDefinition';
                    key: string;
                    value: string;
                  }>;
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
                }
              | {
                  __typename: 'SolidDefinition';
                  name: string;
                  description: string | null;
                  metadata: Array<{
                    __typename: 'MetadataItemDefinition';
                    key: string;
                    value: string;
                  }>;
                  requiredResources: Array<{
                    __typename: 'ResourceRequirement';
                    resourceKey: string;
                  }>;
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
            inputs: Array<{
              __typename: 'Input';
              isDynamicCollect: boolean;
              definition: {
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
              };
              dependsOn: Array<{
                __typename: 'Output';
                definition: {__typename: 'OutputDefinition'; name: string};
                solid: {__typename: 'Solid'; name: string};
              }>;
            }>;
            outputs: Array<{
              __typename: 'Output';
              definition: {
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
              };
              dependedBy: Array<{
                __typename: 'Input';
                definition: {__typename: 'InputDefinition'; name: string};
                solid: {__typename: 'Solid'; name: string};
              }>;
            }>;
          };
        } | null;
      }
    | {__typename: 'PipelineNotFoundError'}
    | {__typename: 'PythonError'};
};

export type SidebarGraphOpQueryVariables = Types.Exact<{
  selector: Types.GraphSelector;
  handleID: Types.Scalars['String'];
}>;

export type SidebarGraphOpQuery = {
  __typename: 'DagitQuery';
  graphOrError:
    | {
        __typename: 'Graph';
        id: string;
        name: string;
        solidHandle: {
          __typename: 'SolidHandle';
          solid: {
            __typename: 'Solid';
            name: string;
            definition:
              | {
                  __typename: 'CompositeSolidDefinition';
                  id: string;
                  name: string;
                  description: string | null;
                  metadata: Array<{
                    __typename: 'MetadataItemDefinition';
                    key: string;
                    value: string;
                  }>;
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
                }
              | {
                  __typename: 'SolidDefinition';
                  name: string;
                  description: string | null;
                  metadata: Array<{
                    __typename: 'MetadataItemDefinition';
                    key: string;
                    value: string;
                  }>;
                  requiredResources: Array<{
                    __typename: 'ResourceRequirement';
                    resourceKey: string;
                  }>;
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
            inputs: Array<{
              __typename: 'Input';
              isDynamicCollect: boolean;
              definition: {
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
              };
              dependsOn: Array<{
                __typename: 'Output';
                definition: {__typename: 'OutputDefinition'; name: string};
                solid: {__typename: 'Solid'; name: string};
              }>;
            }>;
            outputs: Array<{
              __typename: 'Output';
              definition: {
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
              };
              dependedBy: Array<{
                __typename: 'Input';
                definition: {__typename: 'InputDefinition'; name: string};
                solid: {__typename: 'Solid'; name: string};
              }>;
            }>;
          };
        } | null;
      }
    | {__typename: 'GraphNotFoundError'}
    | {__typename: 'PythonError'};
};
