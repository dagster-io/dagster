// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type UsedSolidDetailsQueryVariables = Types.Exact<{
  name: Types.Scalars['String'];
  repositorySelector: Types.RepositorySelector;
}>;

export type UsedSolidDetailsQuery = {
  __typename: 'Query';
  repositoryOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Repository';
        id: string;
        usedSolid: {
          __typename: 'UsedSolid';
          definition:
            | {
                __typename: 'CompositeSolidDefinition';
                name: string;
                description: string | null;
                id: string;
                metadata: Array<{__typename: 'MetadataItemDefinition'; key: string; value: string}>;
                inputDefinitions: Array<{
                  __typename: 'InputDefinition';
                  name: string;
                  description: string | null;
                  type:
                    | {
                        __typename: 'ListDagsterType';
                        displayName: string;
                        name: string | null;
                        description: string | null;
                      }
                    | {
                        __typename: 'NullableDagsterType';
                        displayName: string;
                        name: string | null;
                        description: string | null;
                      }
                    | {
                        __typename: 'RegularDagsterType';
                        displayName: string;
                        name: string | null;
                        description: string | null;
                      };
                }>;
                outputDefinitions: Array<{
                  __typename: 'OutputDefinition';
                  name: string;
                  description: string | null;
                  isDynamic: boolean | null;
                  type:
                    | {
                        __typename: 'ListDagsterType';
                        displayName: string;
                        name: string | null;
                        description: string | null;
                      }
                    | {
                        __typename: 'NullableDagsterType';
                        displayName: string;
                        name: string | null;
                        description: string | null;
                      }
                    | {
                        __typename: 'RegularDagsterType';
                        displayName: string;
                        name: string | null;
                        description: string | null;
                      };
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
              }
            | {
                __typename: 'SolidDefinition';
                name: string;
                description: string | null;
                metadata: Array<{__typename: 'MetadataItemDefinition'; key: string; value: string}>;
                inputDefinitions: Array<{
                  __typename: 'InputDefinition';
                  name: string;
                  description: string | null;
                  type:
                    | {
                        __typename: 'ListDagsterType';
                        displayName: string;
                        name: string | null;
                        description: string | null;
                      }
                    | {
                        __typename: 'NullableDagsterType';
                        displayName: string;
                        name: string | null;
                        description: string | null;
                      }
                    | {
                        __typename: 'RegularDagsterType';
                        displayName: string;
                        name: string | null;
                        description: string | null;
                      };
                }>;
                outputDefinitions: Array<{
                  __typename: 'OutputDefinition';
                  name: string;
                  description: string | null;
                  isDynamic: boolean | null;
                  type:
                    | {
                        __typename: 'ListDagsterType';
                        displayName: string;
                        name: string | null;
                        description: string | null;
                      }
                    | {
                        __typename: 'NullableDagsterType';
                        displayName: string;
                        name: string | null;
                        description: string | null;
                      }
                    | {
                        __typename: 'RegularDagsterType';
                        displayName: string;
                        name: string | null;
                        description: string | null;
                      };
                }>;
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
                        key: string;
                        description: string | null;
                        givenName: string;
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
                        key: string;
                        description: string | null;
                        keyLabelName: string | null;
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
                        key: string;
                        description: string | null;
                        givenName: string;
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
                        key: string;
                        description: string | null;
                        scalarTypeKey: string;
                        nonScalarTypeKey: string;
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
              };
          invocations: Array<{
            __typename: 'NodeInvocationSite';
            pipeline: {__typename: 'Pipeline'; id: string; name: string};
            solidHandle: {__typename: 'SolidHandle'; handleID: string};
          }>;
        } | null;
      }
    | {__typename: 'RepositoryNotFoundError'};
};
