// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type PipelineRunLogsSubscriptionVariables = Types.Exact<{
  runId: Types.Scalars['ID']['input'];
  cursor?: Types.InputMaybe<Types.Scalars['String']['input']>;
}>;

export type PipelineRunLogsSubscription = {
  __typename: 'Subscription';
  pipelineRunLogs:
    | {
        __typename: 'PipelineRunLogsSubscriptionFailure';
        missingRunId: string | null;
        message: string;
      }
    | {
        __typename: 'PipelineRunLogsSubscriptionSuccess';
        hasMorePastEvents: boolean;
        cursor: string;
        messages: Array<
          | {
              __typename: 'AlertFailureEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'AlertStartEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'AlertSuccessEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'AssetCheckEvaluationEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              evaluation: {
                __typename: 'AssetCheckEvaluation';
                checkName: string;
                success: boolean;
                timestamp: number;
                assetKey: {__typename: 'AssetKey'; path: Array<string>};
                targetMaterialization: {
                  __typename: 'AssetCheckEvaluationTargetMaterializationData';
                  timestamp: number;
                } | null;
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
              };
            }
          | {
              __typename: 'AssetCheckEvaluationPlannedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'AssetMaterializationPlannedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'EngineEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              markerStart: string | null;
              markerEnd: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
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
              error: {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              } | null;
            }
          | {
              __typename: 'ExecutionStepFailureEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              errorSource: Types.ErrorSource | null;
              error: {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              } | null;
              failureMetadata: {
                __typename: 'FailureMetadata';
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
              } | null;
            }
          | {
              __typename: 'ExecutionStepInputEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              inputName: string;
              typeCheck: {
                __typename: 'TypeCheck';
                label: string | null;
                description: string | null;
                success: boolean;
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
              };
            }
          | {
              __typename: 'ExecutionStepOutputEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              outputName: string;
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
              typeCheck: {
                __typename: 'TypeCheck';
                label: string | null;
                description: string | null;
                success: boolean;
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
              };
            }
          | {
              __typename: 'ExecutionStepRestartEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ExecutionStepSkippedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ExecutionStepStartEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ExecutionStepSuccessEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ExecutionStepUpForRetryEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              error: {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              } | null;
            }
          | {
              __typename: 'HandledOutputEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              outputName: string;
              managerKey: string;
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
              __typename: 'HookCompletedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'HookErroredEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              error: {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              } | null;
            }
          | {
              __typename: 'HookSkippedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'LoadedInputEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              inputName: string;
              managerKey: string;
              upstreamOutputName: string | null;
              upstreamStepKey: string | null;
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
              __typename: 'LogMessageEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'LogsCapturedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              fileKey: string;
              stepKeys: Array<string> | null;
              pid: number | null;
              externalStdoutUrl: string | null;
              externalStderrUrl: string | null;
              eventType: Types.DagsterEventType | null;
              externalUrl: string | null;
            }
          | {
              __typename: 'MaterializationEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
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
              assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
            }
          | {
              __typename: 'ObjectStoreOperationEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              operationResult: {
                __typename: 'ObjectStoreOperationResult';
                op: Types.ObjectStoreOperationType;
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
              };
            }
          | {
              __typename: 'ObservationEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
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
              assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
            }
          | {
              __typename: 'ResourceInitFailureEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              markerStart: string | null;
              markerEnd: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
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
              error: {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              } | null;
            }
          | {
              __typename: 'ResourceInitStartedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              markerStart: string | null;
              markerEnd: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
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
              __typename: 'ResourceInitSuccessEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              markerStart: string | null;
              markerEnd: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
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
              __typename: 'RunCanceledEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunCancelingEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunDequeuedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunEnqueuedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunFailureEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              error: {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              } | null;
            }
          | {
              __typename: 'RunStartEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunStartingEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunSuccessEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'StepExpectationResultEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              expectationResult: {
                __typename: 'ExpectationResult';
                success: boolean;
                label: string | null;
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
              };
            }
          | {
              __typename: 'StepWorkerStartedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              markerStart: string | null;
              markerEnd: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
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
              __typename: 'StepWorkerStartingEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              markerStart: string | null;
              markerEnd: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
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
        >;
      };
};

export type RunLogsSubscriptionSuccessFragment = {
  __typename: 'PipelineRunLogsSubscriptionSuccess';
  hasMorePastEvents: boolean;
  cursor: string;
  messages: Array<
    | {
        __typename: 'AlertFailureEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'AlertStartEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'AlertSuccessEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'AssetCheckEvaluationEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        evaluation: {
          __typename: 'AssetCheckEvaluation';
          checkName: string;
          success: boolean;
          timestamp: number;
          assetKey: {__typename: 'AssetKey'; path: Array<string>};
          targetMaterialization: {
            __typename: 'AssetCheckEvaluationTargetMaterializationData';
            timestamp: number;
          } | null;
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
        };
      }
    | {
        __typename: 'AssetCheckEvaluationPlannedEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'AssetMaterializationPlannedEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'EngineEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        markerStart: string | null;
        markerEnd: string | null;
        eventType: Types.DagsterEventType | null;
        label: string | null;
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
        error: {
          __typename: 'PythonError';
          message: string;
          stack: Array<string>;
          errorChain: Array<{
            __typename: 'ErrorChainLink';
            isExplicitLink: boolean;
            error: {__typename: 'PythonError'; message: string; stack: Array<string>};
          }>;
        } | null;
      }
    | {
        __typename: 'ExecutionStepFailureEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        errorSource: Types.ErrorSource | null;
        error: {
          __typename: 'PythonError';
          message: string;
          stack: Array<string>;
          errorChain: Array<{
            __typename: 'ErrorChainLink';
            isExplicitLink: boolean;
            error: {__typename: 'PythonError'; message: string; stack: Array<string>};
          }>;
        } | null;
        failureMetadata: {
          __typename: 'FailureMetadata';
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
        } | null;
      }
    | {
        __typename: 'ExecutionStepInputEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        inputName: string;
        typeCheck: {
          __typename: 'TypeCheck';
          label: string | null;
          description: string | null;
          success: boolean;
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
        };
      }
    | {
        __typename: 'ExecutionStepOutputEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        label: string | null;
        description: string | null;
        outputName: string;
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
        typeCheck: {
          __typename: 'TypeCheck';
          label: string | null;
          description: string | null;
          success: boolean;
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
        };
      }
    | {
        __typename: 'ExecutionStepRestartEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'ExecutionStepSkippedEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'ExecutionStepStartEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'ExecutionStepSuccessEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'ExecutionStepUpForRetryEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        error: {
          __typename: 'PythonError';
          message: string;
          stack: Array<string>;
          errorChain: Array<{
            __typename: 'ErrorChainLink';
            isExplicitLink: boolean;
            error: {__typename: 'PythonError'; message: string; stack: Array<string>};
          }>;
        } | null;
      }
    | {
        __typename: 'HandledOutputEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        label: string | null;
        description: string | null;
        outputName: string;
        managerKey: string;
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
      }
    | {
        __typename: 'HookCompletedEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'HookErroredEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        error: {
          __typename: 'PythonError';
          message: string;
          stack: Array<string>;
          errorChain: Array<{
            __typename: 'ErrorChainLink';
            isExplicitLink: boolean;
            error: {__typename: 'PythonError'; message: string; stack: Array<string>};
          }>;
        } | null;
      }
    | {
        __typename: 'HookSkippedEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'LoadedInputEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        label: string | null;
        description: string | null;
        inputName: string;
        managerKey: string;
        upstreamOutputName: string | null;
        upstreamStepKey: string | null;
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
      }
    | {
        __typename: 'LogMessageEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'LogsCapturedEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        fileKey: string;
        stepKeys: Array<string> | null;
        pid: number | null;
        externalStdoutUrl: string | null;
        externalStderrUrl: string | null;
        eventType: Types.DagsterEventType | null;
        externalUrl: string | null;
      }
    | {
        __typename: 'MaterializationEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        label: string | null;
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
        assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
      }
    | {
        __typename: 'ObjectStoreOperationEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        operationResult: {
          __typename: 'ObjectStoreOperationResult';
          op: Types.ObjectStoreOperationType;
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
        };
      }
    | {
        __typename: 'ObservationEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        label: string | null;
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
        assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
      }
    | {
        __typename: 'ResourceInitFailureEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        markerStart: string | null;
        markerEnd: string | null;
        eventType: Types.DagsterEventType | null;
        label: string | null;
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
        error: {
          __typename: 'PythonError';
          message: string;
          stack: Array<string>;
          errorChain: Array<{
            __typename: 'ErrorChainLink';
            isExplicitLink: boolean;
            error: {__typename: 'PythonError'; message: string; stack: Array<string>};
          }>;
        } | null;
      }
    | {
        __typename: 'ResourceInitStartedEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        markerStart: string | null;
        markerEnd: string | null;
        eventType: Types.DagsterEventType | null;
        label: string | null;
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
      }
    | {
        __typename: 'ResourceInitSuccessEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        markerStart: string | null;
        markerEnd: string | null;
        eventType: Types.DagsterEventType | null;
        label: string | null;
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
      }
    | {
        __typename: 'RunCanceledEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'RunCancelingEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'RunDequeuedEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'RunEnqueuedEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'RunFailureEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        error: {
          __typename: 'PythonError';
          message: string;
          stack: Array<string>;
          errorChain: Array<{
            __typename: 'ErrorChainLink';
            isExplicitLink: boolean;
            error: {__typename: 'PythonError'; message: string; stack: Array<string>};
          }>;
        } | null;
      }
    | {
        __typename: 'RunStartEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'RunStartingEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'RunSuccessEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
      }
    | {
        __typename: 'StepExpectationResultEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        eventType: Types.DagsterEventType | null;
        expectationResult: {
          __typename: 'ExpectationResult';
          success: boolean;
          label: string | null;
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
        };
      }
    | {
        __typename: 'StepWorkerStartedEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        markerStart: string | null;
        markerEnd: string | null;
        eventType: Types.DagsterEventType | null;
        label: string | null;
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
      }
    | {
        __typename: 'StepWorkerStartingEvent';
        runId: string;
        message: string;
        timestamp: string;
        level: Types.LogLevel;
        stepKey: string | null;
        markerStart: string | null;
        markerEnd: string | null;
        eventType: Types.DagsterEventType | null;
        label: string | null;
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
      }
  >;
};

export type PipelineRunLogsSubscriptionStatusFragment = {
  __typename: 'Run';
  id: string;
  status: Types.RunStatus;
  canTerminate: boolean;
};

export type RunLogsQueryVariables = Types.Exact<{
  runId: Types.Scalars['ID']['input'];
  cursor?: Types.InputMaybe<Types.Scalars['String']['input']>;
  limit?: Types.InputMaybe<Types.Scalars['Int']['input']>;
}>;

export type RunLogsQuery = {
  __typename: 'Query';
  pipelineRunOrError:
    | {__typename: 'PythonError'}
    | {__typename: 'Run'; id: string; status: Types.RunStatus; canTerminate: boolean}
    | {__typename: 'RunNotFoundError'};
  logsForRun:
    | {
        __typename: 'EventConnection';
        cursor: string;
        events: Array<
          | {
              __typename: 'AlertFailureEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'AlertStartEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'AlertSuccessEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'AssetCheckEvaluationEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              evaluation: {
                __typename: 'AssetCheckEvaluation';
                checkName: string;
                success: boolean;
                timestamp: number;
                assetKey: {__typename: 'AssetKey'; path: Array<string>};
                targetMaterialization: {
                  __typename: 'AssetCheckEvaluationTargetMaterializationData';
                  timestamp: number;
                } | null;
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
              };
            }
          | {
              __typename: 'AssetCheckEvaluationPlannedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'AssetMaterializationPlannedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'EngineEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              markerStart: string | null;
              markerEnd: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
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
              error: {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              } | null;
            }
          | {
              __typename: 'ExecutionStepFailureEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              errorSource: Types.ErrorSource | null;
              error: {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              } | null;
              failureMetadata: {
                __typename: 'FailureMetadata';
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
              } | null;
            }
          | {
              __typename: 'ExecutionStepInputEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              inputName: string;
              typeCheck: {
                __typename: 'TypeCheck';
                label: string | null;
                description: string | null;
                success: boolean;
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
              };
            }
          | {
              __typename: 'ExecutionStepOutputEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              outputName: string;
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
              typeCheck: {
                __typename: 'TypeCheck';
                label: string | null;
                description: string | null;
                success: boolean;
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
              };
            }
          | {
              __typename: 'ExecutionStepRestartEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ExecutionStepSkippedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ExecutionStepStartEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ExecutionStepSuccessEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ExecutionStepUpForRetryEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              error: {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              } | null;
            }
          | {
              __typename: 'HandledOutputEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              outputName: string;
              managerKey: string;
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
              __typename: 'HookCompletedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'HookErroredEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              error: {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              } | null;
            }
          | {
              __typename: 'HookSkippedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'LoadedInputEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
              description: string | null;
              inputName: string;
              managerKey: string;
              upstreamOutputName: string | null;
              upstreamStepKey: string | null;
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
              __typename: 'LogMessageEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'LogsCapturedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              fileKey: string;
              stepKeys: Array<string> | null;
              pid: number | null;
              externalStdoutUrl: string | null;
              externalStderrUrl: string | null;
              eventType: Types.DagsterEventType | null;
              externalUrl: string | null;
            }
          | {
              __typename: 'MaterializationEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
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
              assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
            }
          | {
              __typename: 'ObjectStoreOperationEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              operationResult: {
                __typename: 'ObjectStoreOperationResult';
                op: Types.ObjectStoreOperationType;
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
              };
            }
          | {
              __typename: 'ObservationEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
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
              assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
            }
          | {
              __typename: 'ResourceInitFailureEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              markerStart: string | null;
              markerEnd: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
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
              error: {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              } | null;
            }
          | {
              __typename: 'ResourceInitStartedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              markerStart: string | null;
              markerEnd: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
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
              __typename: 'ResourceInitSuccessEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              markerStart: string | null;
              markerEnd: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
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
              __typename: 'RunCanceledEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunCancelingEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunDequeuedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunEnqueuedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunFailureEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              error: {
                __typename: 'PythonError';
                message: string;
                stack: Array<string>;
                errorChain: Array<{
                  __typename: 'ErrorChainLink';
                  isExplicitLink: boolean;
                  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
                }>;
              } | null;
            }
          | {
              __typename: 'RunStartEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunStartingEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunSuccessEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'StepExpectationResultEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
              expectationResult: {
                __typename: 'ExpectationResult';
                success: boolean;
                label: string | null;
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
              };
            }
          | {
              __typename: 'StepWorkerStartedEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              markerStart: string | null;
              markerEnd: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
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
              __typename: 'StepWorkerStartingEvent';
              runId: string;
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              markerStart: string | null;
              markerEnd: string | null;
              eventType: Types.DagsterEventType | null;
              label: string | null;
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
        >;
      }
    | {__typename: 'PythonError'; message: string; stack: Array<string>}
    | {__typename: 'RunNotFoundError'};
};
