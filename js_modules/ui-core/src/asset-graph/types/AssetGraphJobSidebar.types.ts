// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetGraphSidebarQueryVariables = Types.Exact<{
  pipelineSelector: Types.PipelineSelector;
}>;

export type AssetGraphSidebarQuery = {
  __typename: 'Query';
  pipelineSnapshotOrError:
    | {__typename: 'PipelineNotFoundError'; message: string}
    | {
        __typename: 'PipelineSnapshot';
        id: string;
        pipelineSnapshotId: string;
        parentSnapshotId: string | null;
        externalJobSource: string | null;
        name: string;
        description: string | null;
        metadataEntries: Array<
          | {
              __typename: 'AssetMetadataEntry';
              label: string;
              description: string | null;
              assetKey: {__typename: 'AssetKey'; path: Array<string>};
            }
          | {
              __typename: 'BoolMetadataEntry';
              boolValue: boolean | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'CodeReferencesMetadataEntry';
              label: string;
              description: string | null;
              codeReferences: Array<
                | {
                    __typename: 'LocalFileCodeReference';
                    filePath: string;
                    lineNumber: number | null;
                    label: string | null;
                  }
                | {__typename: 'UrlCodeReference'; url: string; label: string | null}
              >;
            }
          | {
              __typename: 'FloatMetadataEntry';
              floatValue: number | null;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'IntMetadataEntry';
              intValue: number | null;
              intRepr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JobMetadataEntry';
              jobName: string;
              repositoryName: string | null;
              locationName: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'JsonMetadataEntry';
              jsonString: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'MarkdownMetadataEntry';
              mdStr: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'NotebookMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
          | {
              __typename: 'PathMetadataEntry';
              path: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PipelineRunMetadataEntry';
              runId: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PoolMetadataEntry';
              pool: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'PythonArtifactMetadataEntry';
              module: string;
              name: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TableColumnLineageMetadataEntry';
              label: string;
              description: string | null;
              lineage: Array<{
                __typename: 'TableColumnLineageEntry';
                columnName: string;
                columnDeps: Array<{
                  __typename: 'TableColumnDep';
                  columnName: string;
                  assetKey: {__typename: 'AssetKey'; path: Array<string>};
                }>;
              }>;
            }
          | {
              __typename: 'TableMetadataEntry';
              label: string;
              description: string | null;
              table: {
                __typename: 'Table';
                records: Array<string>;
                schema: {
                  __typename: 'TableSchema';
                  columns: Array<{
                    __typename: 'TableColumn';
                    name: string;
                    description: string | null;
                    type: string;
                    tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                    constraints: {
                      __typename: 'TableColumnConstraints';
                      nullable: boolean;
                      unique: boolean;
                      other: Array<string>;
                    };
                  }>;
                  constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
                };
              };
            }
          | {
              __typename: 'TableSchemaMetadataEntry';
              label: string;
              description: string | null;
              schema: {
                __typename: 'TableSchema';
                columns: Array<{
                  __typename: 'TableColumn';
                  name: string;
                  description: string | null;
                  type: string;
                  tags: Array<{__typename: 'DefinitionTag'; key: string; value: string}>;
                  constraints: {
                    __typename: 'TableColumnConstraints';
                    nullable: boolean;
                    unique: boolean;
                    other: Array<string>;
                  };
                }>;
                constraints: {__typename: 'TableConstraints'; other: Array<string>} | null;
              };
            }
          | {
              __typename: 'TextMetadataEntry';
              text: string;
              label: string;
              description: string | null;
            }
          | {
              __typename: 'TimestampMetadataEntry';
              timestamp: number;
              label: string;
              description: string | null;
            }
          | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
        >;
        tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
        owners: Array<
          | {__typename: 'TeamDefinitionOwner'; team: string}
          | {__typename: 'UserDefinitionOwner'; email: string}
        >;
        modes: Array<{
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
        }>;
      }
    | {__typename: 'PipelineSnapshotNotFoundError'; message: string}
    | {
        __typename: 'PythonError';
        message: string;
        stack: Array<string>;
        errorChain: Array<{
          __typename: 'ErrorChainLink';
          isExplicitLink: boolean;
          error: {__typename: 'PythonError'; message: string; stack: Array<string>};
        }>;
      };
};

export const AssetGraphSidebarQueryVersion = '423d6b155cc63752472fa9bde2ff75a6e872fa1c230473394bdf6057789ad9e8';
