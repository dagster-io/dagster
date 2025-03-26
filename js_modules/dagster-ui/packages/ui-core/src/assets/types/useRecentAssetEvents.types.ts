// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetFailedToMaterializeFragment = {
  __typename: 'FailedToMaterializeEvent';
  runId: string;
  timestamp: string;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  partition: string | null;
  tags: Array<{__typename: 'EventTag'; key: string; value: string}>;
  runOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Run';
        id: string;
        mode: string;
        status: Types.RunStatus;
        pipelineName: string;
        pipelineSnapshotId: string | null;
        repositoryOrigin: {
          __typename: 'RepositoryOrigin';
          id: string;
          repositoryName: string;
          repositoryLocationName: string;
        } | null;
      }
    | {__typename: 'RunNotFoundError'};
  assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
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
    | {__typename: 'NotebookMetadataEntry'; path: string; label: string; description: string | null}
    | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
    | {__typename: 'PathMetadataEntry'; path: string; label: string; description: string | null}
    | {
        __typename: 'PipelineRunMetadataEntry';
        runId: string;
        label: string;
        description: string | null;
      }
    | {__typename: 'PoolMetadataEntry'; pool: string; label: string; description: string | null}
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
    | {__typename: 'TextMetadataEntry'; text: string; label: string; description: string | null}
    | {
        __typename: 'TimestampMetadataEntry';
        timestamp: number;
        label: string;
        description: string | null;
      }
    | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
  >;
};

export type AssetSuccessfulMaterializationFragment = {
  __typename: 'MaterializationEvent';
  partition: string | null;
  runId: string;
  timestamp: string;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  tags: Array<{__typename: 'EventTag'; key: string; value: string}>;
  runOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Run';
        id: string;
        mode: string;
        status: Types.RunStatus;
        pipelineName: string;
        pipelineSnapshotId: string | null;
        repositoryOrigin: {
          __typename: 'RepositoryOrigin';
          id: string;
          repositoryName: string;
          repositoryLocationName: string;
        } | null;
      }
    | {__typename: 'RunNotFoundError'};
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
    | {__typename: 'NotebookMetadataEntry'; path: string; label: string; description: string | null}
    | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
    | {__typename: 'PathMetadataEntry'; path: string; label: string; description: string | null}
    | {
        __typename: 'PipelineRunMetadataEntry';
        runId: string;
        label: string;
        description: string | null;
      }
    | {__typename: 'PoolMetadataEntry'; pool: string; label: string; description: string | null}
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
    | {__typename: 'TextMetadataEntry'; text: string; label: string; description: string | null}
    | {
        __typename: 'TimestampMetadataEntry';
        timestamp: number;
        label: string;
        description: string | null;
      }
    | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
  >;
  assetLineage: Array<{
    __typename: 'AssetLineageInfo';
    partitions: Array<string>;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
  }>;
};

export type AssetObservationFragment = {
  __typename: 'ObservationEvent';
  partition: string | null;
  runId: string;
  timestamp: string;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  tags: Array<{__typename: 'EventTag'; key: string; value: string}>;
  runOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Run';
        id: string;
        mode: string;
        status: Types.RunStatus;
        pipelineName: string;
        pipelineSnapshotId: string | null;
        repositoryOrigin: {
          __typename: 'RepositoryOrigin';
          id: string;
          repositoryName: string;
          repositoryLocationName: string;
        } | null;
      }
    | {__typename: 'RunNotFoundError'};
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
    | {__typename: 'NotebookMetadataEntry'; path: string; label: string; description: string | null}
    | {__typename: 'NullMetadataEntry'; label: string; description: string | null}
    | {__typename: 'PathMetadataEntry'; path: string; label: string; description: string | null}
    | {
        __typename: 'PipelineRunMetadataEntry';
        runId: string;
        label: string;
        description: string | null;
      }
    | {__typename: 'PoolMetadataEntry'; pool: string; label: string; description: string | null}
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
    | {__typename: 'TextMetadataEntry'; text: string; label: string; description: string | null}
    | {
        __typename: 'TimestampMetadataEntry';
        timestamp: number;
        label: string;
        description: string | null;
      }
    | {__typename: 'UrlMetadataEntry'; url: string; label: string; description: string | null}
  >;
};

export type AssetEventsQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
  eventTypeSelector: Types.MaterializationHistoryEventTypeSelector;
  limit?: Types.InputMaybe<Types.Scalars['Int']['input']>;
  before?: Types.InputMaybe<Types.Scalars['String']['input']>;
}>;

export type AssetEventsQuery = {
  __typename: 'Query';
  assetOrError:
    | {
        __typename: 'Asset';
        id: string;
        key: {__typename: 'AssetKey'; path: Array<string>};
        assetObservations: Array<{
          __typename: 'ObservationEvent';
          partition: string | null;
          runId: string;
          timestamp: string;
          stepKey: string | null;
          label: string | null;
          description: string | null;
          tags: Array<{__typename: 'EventTag'; key: string; value: string}>;
          runOrError:
            | {__typename: 'PythonError'}
            | {
                __typename: 'Run';
                id: string;
                mode: string;
                status: Types.RunStatus;
                pipelineName: string;
                pipelineSnapshotId: string | null;
                repositoryOrigin: {
                  __typename: 'RepositoryOrigin';
                  id: string;
                  repositoryName: string;
                  repositoryLocationName: string;
                } | null;
              }
            | {__typename: 'RunNotFoundError'};
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
            | {
                __typename: 'UrlMetadataEntry';
                url: string;
                label: string;
                description: string | null;
              }
          >;
        }>;
        assetMaterializationHistory: {
          __typename: 'MaterializationHistoryConnection';
          cursor: string;
          results: Array<
            | {
                __typename: 'FailedToMaterializeEvent';
                runId: string;
                timestamp: string;
                stepKey: string | null;
                label: string | null;
                description: string | null;
                partition: string | null;
                tags: Array<{__typename: 'EventTag'; key: string; value: string}>;
                runOrError:
                  | {__typename: 'PythonError'}
                  | {
                      __typename: 'Run';
                      id: string;
                      mode: string;
                      status: Types.RunStatus;
                      pipelineName: string;
                      pipelineSnapshotId: string | null;
                      repositoryOrigin: {
                        __typename: 'RepositoryOrigin';
                        id: string;
                        repositoryName: string;
                        repositoryLocationName: string;
                      } | null;
                    }
                  | {__typename: 'RunNotFoundError'};
                assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
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
                          constraints: {
                            __typename: 'TableConstraints';
                            other: Array<string>;
                          } | null;
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
                  | {
                      __typename: 'UrlMetadataEntry';
                      url: string;
                      label: string;
                      description: string | null;
                    }
                >;
              }
            | {
                __typename: 'MaterializationEvent';
                partition: string | null;
                runId: string;
                timestamp: string;
                stepKey: string | null;
                label: string | null;
                description: string | null;
                tags: Array<{__typename: 'EventTag'; key: string; value: string}>;
                runOrError:
                  | {__typename: 'PythonError'}
                  | {
                      __typename: 'Run';
                      id: string;
                      mode: string;
                      status: Types.RunStatus;
                      pipelineName: string;
                      pipelineSnapshotId: string | null;
                      repositoryOrigin: {
                        __typename: 'RepositoryOrigin';
                        id: string;
                        repositoryName: string;
                        repositoryLocationName: string;
                      } | null;
                    }
                  | {__typename: 'RunNotFoundError'};
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
                          constraints: {
                            __typename: 'TableConstraints';
                            other: Array<string>;
                          } | null;
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
                  | {
                      __typename: 'UrlMetadataEntry';
                      url: string;
                      label: string;
                      description: string | null;
                    }
                >;
                assetLineage: Array<{
                  __typename: 'AssetLineageInfo';
                  partitions: Array<string>;
                  assetKey: {__typename: 'AssetKey'; path: Array<string>};
                }>;
              }
          >;
        };
        definition: {__typename: 'AssetNode'; id: string; partitionKeys: Array<string>} | null;
      }
    | {__typename: 'AssetNotFoundError'};
};

export type RecentAssetEventsQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
  eventTypeSelector: Types.MaterializationHistoryEventTypeSelector;
  limit?: Types.InputMaybe<Types.Scalars['Int']['input']>;
  before?: Types.InputMaybe<Types.Scalars['String']['input']>;
}>;

export type RecentAssetEventsQuery = {
  __typename: 'Query';
  assetOrError:
    | {
        __typename: 'Asset';
        id: string;
        key: {__typename: 'AssetKey'; path: Array<string>};
        assetObservations: Array<{
          __typename: 'ObservationEvent';
          partition: string | null;
          runId: string;
          timestamp: string;
          stepKey: string | null;
          label: string | null;
          description: string | null;
          tags: Array<{__typename: 'EventTag'; key: string; value: string}>;
          runOrError:
            | {__typename: 'PythonError'}
            | {
                __typename: 'Run';
                id: string;
                mode: string;
                status: Types.RunStatus;
                pipelineName: string;
                pipelineSnapshotId: string | null;
                repositoryOrigin: {
                  __typename: 'RepositoryOrigin';
                  id: string;
                  repositoryName: string;
                  repositoryLocationName: string;
                } | null;
              }
            | {__typename: 'RunNotFoundError'};
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
            | {
                __typename: 'UrlMetadataEntry';
                url: string;
                label: string;
                description: string | null;
              }
          >;
        }>;
        assetMaterializationHistory: {
          __typename: 'MaterializationHistoryConnection';
          cursor: string;
          results: Array<
            | {
                __typename: 'FailedToMaterializeEvent';
                runId: string;
                timestamp: string;
                stepKey: string | null;
                label: string | null;
                description: string | null;
                partition: string | null;
                tags: Array<{__typename: 'EventTag'; key: string; value: string}>;
                runOrError:
                  | {__typename: 'PythonError'}
                  | {
                      __typename: 'Run';
                      id: string;
                      mode: string;
                      status: Types.RunStatus;
                      pipelineName: string;
                      pipelineSnapshotId: string | null;
                      repositoryOrigin: {
                        __typename: 'RepositoryOrigin';
                        id: string;
                        repositoryName: string;
                        repositoryLocationName: string;
                      } | null;
                    }
                  | {__typename: 'RunNotFoundError'};
                assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
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
                          constraints: {
                            __typename: 'TableConstraints';
                            other: Array<string>;
                          } | null;
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
                  | {
                      __typename: 'UrlMetadataEntry';
                      url: string;
                      label: string;
                      description: string | null;
                    }
                >;
              }
            | {
                __typename: 'MaterializationEvent';
                partition: string | null;
                runId: string;
                timestamp: string;
                stepKey: string | null;
                label: string | null;
                description: string | null;
                tags: Array<{__typename: 'EventTag'; key: string; value: string}>;
                runOrError:
                  | {__typename: 'PythonError'}
                  | {
                      __typename: 'Run';
                      id: string;
                      mode: string;
                      status: Types.RunStatus;
                      pipelineName: string;
                      pipelineSnapshotId: string | null;
                      repositoryOrigin: {
                        __typename: 'RepositoryOrigin';
                        id: string;
                        repositoryName: string;
                        repositoryLocationName: string;
                      } | null;
                    }
                  | {__typename: 'RunNotFoundError'};
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
                          constraints: {
                            __typename: 'TableConstraints';
                            other: Array<string>;
                          } | null;
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
                  | {
                      __typename: 'UrlMetadataEntry';
                      url: string;
                      label: string;
                      description: string | null;
                    }
                >;
                assetLineage: Array<{
                  __typename: 'AssetLineageInfo';
                  partitions: Array<string>;
                  assetKey: {__typename: 'AssetKey'; path: Array<string>};
                }>;
              }
          >;
        };
      }
    | {__typename: 'AssetNotFoundError'};
};

export type AssetPartitionEventsQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
  partitions: Array<Types.Scalars['String']['input']> | Types.Scalars['String']['input'];
}>;

export type AssetPartitionEventsQuery = {
  __typename: 'Query';
  assetNodeOrError:
    | {
        __typename: 'AssetNode';
        id: string;
        latestMaterializationByPartition: Array<{
          __typename: 'MaterializationEvent';
          partition: string | null;
          runId: string;
          timestamp: string;
          stepKey: string | null;
          label: string | null;
          description: string | null;
          tags: Array<{__typename: 'EventTag'; key: string; value: string}>;
          runOrError:
            | {__typename: 'PythonError'}
            | {
                __typename: 'Run';
                id: string;
                mode: string;
                status: Types.RunStatus;
                pipelineName: string;
                pipelineSnapshotId: string | null;
                repositoryOrigin: {
                  __typename: 'RepositoryOrigin';
                  id: string;
                  repositoryName: string;
                  repositoryLocationName: string;
                } | null;
              }
            | {__typename: 'RunNotFoundError'};
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
            | {
                __typename: 'UrlMetadataEntry';
                url: string;
                label: string;
                description: string | null;
              }
          >;
          assetLineage: Array<{
            __typename: 'AssetLineageInfo';
            partitions: Array<string>;
            assetKey: {__typename: 'AssetKey'; path: Array<string>};
          }>;
        } | null>;
      }
    | {__typename: 'AssetNotFoundError'};
};

export type LatestAssetPartitionsQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
  limit: Types.Scalars['Int']['input'];
}>;

export type LatestAssetPartitionsQuery = {
  __typename: 'Query';
  assetNodeOrError:
    | {
        __typename: 'AssetNode';
        id: string;
        partitionKeyConnection: {
          __typename: 'PartitionKeyConnection';
          results: Array<string>;
        } | null;
      }
    | {__typename: 'AssetNotFoundError'};
};

export const AssetEventsQueryVersion = '748a4d3c4c277a680346a17ce61a72c340a3eca6f8173dceeec833aa02bd7081';

export const RecentAssetEventsQueryVersion = '78b2afdb1284efa23c098cf24cb9324bb2003661327a7981069e4ad966b00af2';

export const AssetPartitionEventsQueryVersion = '859d8d8bf982cc539c932d2fc071b373ca9836cfd083e3fab616d149e1b18646';

export const LatestAssetPartitionsQueryVersion = '2568dc5d6ad01d1695e9b6028a69e20785b90e152b15e84efe76b7c2595707da';
