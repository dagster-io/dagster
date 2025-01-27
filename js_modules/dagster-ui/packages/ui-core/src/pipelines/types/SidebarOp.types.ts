// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type SidebarOpFragment_CompositeSolidDefinition = {
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
            pools: Array<string>;
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
          }
        | {
            __typename: 'SolidDefinition';
            name: string;
            description: string | null;
            pools: Array<string>;
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

export type SidebarOpFragment_Graph = {
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
            pools: Array<string>;
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
          }
        | {
            __typename: 'SolidDefinition';
            name: string;
            description: string | null;
            pools: Array<string>;
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

export type SidebarOpFragment_Job = {
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
            pools: Array<string>;
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
          }
        | {
            __typename: 'SolidDefinition';
            name: string;
            description: string | null;
            pools: Array<string>;
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

export type SidebarOpFragment_Pipeline = {
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
            pools: Array<string>;
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
          }
        | {
            __typename: 'SolidDefinition';
            name: string;
            description: string | null;
            pools: Array<string>;
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

export type SidebarOpFragment_PipelineSnapshot = {
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
            pools: Array<string>;
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
          }
        | {
            __typename: 'SolidDefinition';
            name: string;
            description: string | null;
            pools: Array<string>;
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
  | SidebarOpFragment_CompositeSolidDefinition
  | SidebarOpFragment_Graph
  | SidebarOpFragment_Job
  | SidebarOpFragment_Pipeline
  | SidebarOpFragment_PipelineSnapshot;

export type SidebarPipelineOpQueryVariables = Types.Exact<{
  selector: Types.PipelineSelector;
  handleID: Types.Scalars['String']['input'];
}>;

export type SidebarPipelineOpQuery = {
  __typename: 'Query';
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
                  pools: Array<string>;
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
                  metadata: Array<{
                    __typename: 'MetadataItemDefinition';
                    key: string;
                    value: string;
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
                  pools: Array<string>;
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
                  metadata: Array<{
                    __typename: 'MetadataItemDefinition';
                    key: string;
                    value: string;
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
  handleID: Types.Scalars['String']['input'];
}>;

export type SidebarGraphOpQuery = {
  __typename: 'Query';
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
                  pools: Array<string>;
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
                  metadata: Array<{
                    __typename: 'MetadataItemDefinition';
                    key: string;
                    value: string;
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
                  pools: Array<string>;
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
                  metadata: Array<{
                    __typename: 'MetadataItemDefinition';
                    key: string;
                    value: string;
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

export const SidebarPipelineOpQueryVersion = 'f2f757259ed45d1f13782138866817a5d8e6dd27e4e64253940a72cb60a345f4';

export const SidebarGraphOpQueryVersion = 'd990aa216ec9ca839d65d14e400e00b57acdebfd96399b4daada499381296d34';
